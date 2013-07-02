# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from calendar import timegm
from datetime import datetime
from importlib import import_module
from os import path as op
import re

import houdini as h
from pkg_resources import DistributionNotFound, iter_entry_points, load_entry_point
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from mynt.containers import Config, Container, Posts
from mynt.exceptions import ConfigException, ContentException, ParserException, RendererException
from mynt.fs import File
from mynt.utils import format_url, get_logger, Item, normpath, slugify, Timer


logger = get_logger('mynt')


class Reader(object):
    def __init__(self, src, dest, site, writer):
        self._writer = writer
        
        self._parsers = {}
        self._extensions = {}
        self._cache = {}
        
        self.src = src
        self.dest = dest
        self.site = site
        
        self._find_parsers()
    
    
    def _find_parsers(self):
        for parser in iter_entry_points('mynt.parsers'):
            try:
                Parser = parser.load()
            except DistributionNotFound as e:
                logger.debug('@@ The %s parser could not be loaded due to a missing requirement: %s.', parser.name, unicode(e))
                
                continue
            
            for extension in Parser.accepts:
                if extension in self._extensions:
                    logger.debug('@@ Multiple parsers for \'%s\' files found, skipping %s.', extension, parser.name)
                    
                    continue
                
                self._extensions[extension] = parser.name
            
            self._parsers[parser.name] = Parser
    
    def _get_content_url(self, url, slug, date, frontmatter):
        subs = {
            '<year>': '%Y',
            '<month>': '%m',
            '<day>': '%d',
            '<i_month>': unicode(date.month),
            '<i_day>': unicode(date.day),
            '<slug>': slug
        }
        
        url = url.replace('%', '%%')
        
        for match, replace in subs.iteritems():
            url = url.replace(match, replace)
        
        for attribute, value in frontmatter.iteritems():
            if isinstance(value, basestring):
                url = url.replace('<{0}>'.format(attribute), slugify(value))
        
        url = date.strftime(url).decode('utf-8')
        
        return format_url(url, url.endswith('/'))
    
    def _get_date(self, mtime, date):
        if not date:
            return mtime
        
        d = [None, None, None, 0, 0]
        
        for i, v in enumerate(date.split('-')):
            d[i] = v
        
        if not d[3]:
            d[3], d[4] = mtime.strftime('%H %M').decode('utf-8').split()
        elif not d[4]:
            d[4] = '{0:02d}'.format(d[4])
        
        return datetime.strptime('-'.join(d), '%Y-%m-%d-%H-%M')
    
    def _get_parser(self, f, parser = None):
        if not parser:
            try:
                parser = self._extensions[f.extension]
            except KeyError:
                raise ParserException('No parser found that accepts \'{0}\' files.'.format(f.extension), 'src: {0}'.format(f.path))
        
        if parser in self._cache:
            return self._cache[parser]
        
        options = self.site.get(parser, None)
        
        if parser in self._parsers:
            Parser = self._parsers[parser](options)
        else:
            try:
                Parser = import_module('mynt.parsers.{0}'.format(parser)).Parser(options)
            except ImportError:
                raise ParserException('The {0} parser could not be found.'.format(parser.name))
        
        self._cache[parser] = Parser
        
        return Parser
    
    def _parse_filename(self, f):
        date, slug = re.match(r'(?:(\d{4}(?:-\d{2}-\d{2}){1,2})-)?(.+)', f.name).groups()
        
        return (
            slugify(slug),
            self._get_date(f.mtime, date)
        )
    
    
    def _parse(self, container):
        for f in container.path:
            Timer.start()
            
            item = Item(f.path)
            
            try:
                frontmatter, bodymatter = re.search(r'\A---\s+^(.+?)$\s+---\s*(.*)\Z', f.content, re.M | re.S).groups()
                frontmatter = Config(frontmatter)
            except AttributeError:
                raise ContentException('Invalid frontmatter.', 'src: {0}'.format(f.path), 'frontmatter must not be empty')
            except ConfigException:
                raise ConfigException('Invalid frontmatter.', 'src: {0}'.format(f.path), 'fontmatter contains invalid YAML')
            
            if 'layout' not in frontmatter:
                raise ContentException('Invalid frontmatter.', 'src: {0}'.format(f.path), 'layout must be set')
            
            parser = self._get_parser(f, frontmatter.get('parser', container.config.get('parser', None)))
            
            slug, date = self._parse_filename(f)
            content = parser.parse(self._writer.from_string(bodymatter, frontmatter))
            
            item['content'] = content
            item['date'] = date.strftime(self.site['date_format']).decode('utf-8')
            item['excerpt'] = re.search(r'\A.*?(?:<p>(.+?)</p>)?', content, re.M | re.S).group(1)
            item['tags'] = []
            item['timestamp'] = timegm(date.utctimetuple())
            
            item.update(frontmatter)
            
            item['url'] = self._get_content_url(container.config['url'], slug, date, frontmatter)
            
            container.add(item)
            
            logger.debug('..  (%.3fs) %s', Timer.stop(), f.path.replace(self.src.path, ''))
        
        container.sort()
        container.tag()
        container.archive()
        
        return container
    
    
    def parse(self):
        posts = self._parse(Posts(self.src, self.site))
        containers = {}
        pages = posts.pages
        
        for name, config in self.site['containers'].iteritems():
            container = self._parse(Container(name, self.src, config))
            
            containers[name] = container
            pages.extend(container.pages)
        
        for f in self.src:
            if f.extension in ('.html', '.htm', '.xml'):
                pages.append((f.path.replace(self.src.path, ''), None, None))
        
        return (posts, containers, pages)

class Writer(object):
    def __init__(self, src, dest, site):
        self.src = src
        self.dest = dest
        self.site = site
        
        self._renderer = self._get_renderer()
    
    
    def _get_path(self, url):
        parts = [self.dest.path] + url.split('/')
        
        if url.endswith('/'):
            parts.append('index.html')
        
        path = normpath(*parts)
        
        if op.commonprefix((self.dest.path, path)) != self.dest.path:
            raise ConfigException('Invalid URL.', 'url: {0}'.format(url), 'path traversal is not allowed')
        
        return path
    
    def _get_renderer(self):
        renderer = self.site['renderer']
        options = self.site.get(renderer, None)
        
        try:
            Renderer = load_entry_point('mynt', 'mynt.renderers', renderer)
        except DistributionNotFound as e:
            raise RendererException('The {0} renderer requires {1}.'.format(renderer, unicode(e)))
        except ImportError:
            try:
                Renderer = import_module('mynt.renderers.{0}'.format(renderer)).Renderer
            except ImportError:
                raise RendererException('The {0} renderer could not be found.'.format(renderer))
        
        return Renderer(self.src.path, options)
    
    def _highlight(self, match):
        language, code = match.groups()
        formatter = HtmlFormatter(linenos = 'table')
        
        code = h.unescape_html(code.encode('utf-8')).decode('utf-8')
        
        try:
            code = highlight(code, get_lexer_by_name(language), formatter)
        except ClassNotFound:
            code = highlight(code, get_lexer_by_name('text'), formatter)
        
        return '<div class="code"><div>{0}</div></div>'.format(code)
    
    def _pygmentize(self, html):
        return re.sub(r'<pre><code[^>]+data-lang="([^>]+)"[^>]*>(.+?)</code></pre>', self._highlight, html, flags = re.S)
    
    
    def from_string(self, string, data = None):
        return self._renderer.from_string(string, data)
    
    def register(self, data):
        self._renderer.register(data)
    
    def render(self, template, data = None, url = None):
        url = url if url is not None else template
        path = self._get_path(url)
        
        try:
            Timer.start()
            
            content = self._renderer.render(template, data)
            
            if self.site['pygmentize']:
                content = self._pygmentize(content)
            
            logger.debug('..  (%.3fs) %s', Timer.stop(), path.replace(self.dest.path, ''))
        except RendererException as e:
            raise RendererException(e.message, '{0} in container item {1}'.format(template, data.get('item', url)))
        
        return File(path, content)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from argparse import ArgumentParser
from calendar import timegm
from copy import deepcopy
from datetime import datetime
from glob import iglob
import logging
from os import chdir, getcwd, path as op
import re
from time import sleep, time

import houdini as h
from pkg_resources import load_entry_point, resource_filename
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from watchdog.observers import Observer

from mynt import __version__
from mynt.containers import Config, Page, Post
from mynt.exceptions import ConfigException, OptionException, PageException, RendererException
from mynt.fs import Directory, EventHandler, File
from mynt.server import RequestHandler, Server
from mynt.utils import absurl, get_logger, normpath, OrderedDict


logger = get_logger('mynt')


class Mynt(object):
    defaults = {
        'archive_layout': None,
        'archives_url': '/',
        'assets_url': '/assets/',
        'base_url': '/',
        'date_format': '%A, %B %d, %Y',
        'domain': None,
        'include': [],
        'markup': 'markdown',
        'parser': 'misaka',
        'posts_url': '/<year>/<month>/<day>/<title>/',
        'pygmentize': True,
        'renderer': 'jinja',
        'tag_layout': None,
        'tags_url': '/',
        'version': __version__
    }
    
    _parser = None
    _renderer = None
    
    archives = OrderedDict()
    config = {}
    pages = []
    posts = []
    tags = OrderedDict()
    
    
    def __init__(self, args = None):
        self._start = time()
        
        self.opts = self._get_opts(args)
        
        logger.setLevel(getattr(logging, self.opts['level'], logging.INFO))
        
        self.opts['func']()
    
    
    def _archive(self, posts):
        archives = OrderedDict()
        
        for post in posts:
            year, month = datetime.utcfromtimestamp(post['timestamp']).strftime('%Y %B').decode('utf-8').split()
            
            if year not in archives:
                archives[year] = {
                    'months': OrderedDict({month: [post]}),
                    'url': self._get_archive_url(year),
                    'year': year
                }
            elif month not in archives[year]['months']:
                archives[year]['months'][month] = [post]
            else:
                archives[year]['months'][month].append(post)
        
        return archives
    
    def _get_archive_url(self, year):
        format = self._get_url_format(self.config['archives_url'].endswith('/'))
        
        return format.format(self.config['archives_url'], year)
    
    def _get_opts(self, args):
        opts = {}
        
        parser = ArgumentParser(description = 'A static blog generator.')
        sub = parser.add_subparsers()
        
        level = parser.add_mutually_exclusive_group()
        
        level.add_argument('-l', '--level', default = b'INFO', type = str.upper, choices = [b'DEBUG', b'INFO', b'WARNING', b'ERROR'], help = 'Sets %(prog)s\'s log level.')
        level.add_argument('-q', '--quiet', action = 'store_const', const = 'ERROR', dest = 'level', help = 'Sets %(prog)s\'s log level to ERROR.')
        level.add_argument('-v', '--verbose', action = 'store_const', const = 'DEBUG', dest = 'level', help = 'Sets %(prog)s\'s log level to DEBUG.')
        
        parser.add_argument('-V', '--version', action = 'version', version = '%(prog)s v{0}'.format(__version__), help = 'Prints %(prog)s\'s version and exits.')
        
        gen = sub.add_parser('gen')
        
        gen.add_argument('src', nargs = '?', default = '.', metavar = 'source', help = 'The directory %(prog)s looks in for source files.')
        gen.add_argument('dest', metavar = 'destination', help = 'The directory %(prog)s outputs to.')
        
        gen.add_argument('--base-url', help = 'Sets the site\'s base URL overriding the config setting.')
        
        force = gen.add_mutually_exclusive_group()
        
        force.add_argument('-c', '--clean', action = 'store_true', help = 'Forces generation by deleting the destination if it exists.')
        force.add_argument('-f', '--force', action = 'store_true', help = 'Forces generation by emptying the destination if it exists.')
        
        gen.set_defaults(func = self.generate)
        
        init = sub.add_parser('init')
        
        init.add_argument('dest', metavar = 'destination', help = 'The directory %(prog)s outputs to.')
        
        init.add_argument('--bare', action = 'store_true', help = 'Initializes a new site without using a theme.')
        init.add_argument('-f', '--force', action = 'store_true', help = 'Forces initialization by deleting the destination if it exists.')
        init.add_argument('-t', '--theme', default = 'dark', help = 'Sets which theme will be used.')
        
        init.set_defaults(func = self.init)
        
        serve = sub.add_parser('serve')
        
        serve.add_argument('src', nargs = '?', default = '.', metavar = 'source', help = 'The directory %(prog)s will serve.')
        
        serve.add_argument('--base-url', default = '/', help = 'Sets the site\'s base URL overriding the config setting.')
        serve.add_argument('-p', '--port', default = 8080, type = int, help = 'Sets the port used by the server.')
        
        serve.set_defaults(func = self.serve)
        
        watch = sub.add_parser('watch')
        
        watch.add_argument('src', nargs = '?', default = '.', metavar = 'source', help = 'The directory %(prog)s looks in for source files.')
        watch.add_argument('dest', metavar = 'destination', help = 'The directory %(prog)s outputs to.')
        
        watch.add_argument('--base-url', help = 'Sets the site\'s base URL overriding the config setting.')
        watch.add_argument('-f', '--force', action = 'store_true', help = 'Forces watching by emptying the destination every time a change is made if it exists.')
        
        watch.set_defaults(func = self.watch)
        
        for option, value in vars(parser.parse_args(args)).iteritems():
            if value is not None:
                if isinstance(option, str):
                    option = option.decode('utf-8')
                
                if isinstance(value, str):
                    value = value.decode('utf-8')
                
                opts[option] = value
        
        return opts
    
    def _get_parser(self):
        try:
            return load_entry_point('mynt', 'mynt.parsers.{0}'.format(self.config['markup']), self.config['parser'])
        except ImportError:
            return __import__('mynt.parsers.{0}.{1}'.format(self.config['markup'], self.config['parser']), globals(), locals(), ['Parser'], -1).Parser
    
    def _get_path(self, url):
        parts = [self.dest.path] + url.split('/')
        
        if url.endswith('/'):
            parts.append('index.html')
        
        return normpath(*parts)
    
    def _get_post_url(self, date, slug):
        subs = {
            '<year>': '%Y',
            '<month>': '%m',
            '<day>': '%d',
            '<i_month>': unicode(date.month),
            '<i_day>': unicode(date.day),
            '<title>': self._slugify(slug)
        }
        
        url = self.config['posts_url'].replace('%', '%%')
        
        for match, replace in subs.iteritems():
            url = url.replace(match, replace)
        
        return date.strftime(url).decode('utf-8')
    
    def _get_renderer(self):
        try:
            return load_entry_point('mynt', 'mynt.renderers', self.config['renderer'])
        except ImportError:
            return __import__('mynt.renderers.{0}'.format(self.config['renderer']), globals(), locals(), ['Renderer'], -1).Renderer
    
    def _get_tag_url(self, name):
        format = self._get_url_format(self.config['tags_url'].endswith('/'))
        
        return format.format(self.config['tags_url'], self._slugify(name))
    
    def _get_theme(self, theme):
        return resource_filename(__name__, 'themes/{0}'.format(theme))
    
    def _get_url_format(self, clean):
        return '{0}{1}/' if clean else '{0}/{1}.html'
    
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
        if not self.config['pygmentize']:
            return html
        
        return re.sub(r'<pre><code[^>]+data-lang="([^>]+)"[^>]*>(.+?)</code></pre>', self._highlight, html, flags = re.S)
    
    def _slugify(self, text):
        slug = re.sub(r'\s+', '-', text.strip())
        slug = re.sub(r'[^a-z0-9\-_.]', '', slug, flags = re.I)
        
        if slug == '..':
            raise PageException('Invalid slug.')
        
        return slug
    
    def _update_config(self):
        self.config = deepcopy(self.defaults)
        
        logger.debug('>> Searching for config')
        
        for ext in ('.yml', '.yaml'):
            f = File(normpath(self.src.path, 'config' + ext))
            
            if f.exists:
                logger.debug('..  found: %s', f.path)
                
                try:
                    self.config.update(Config(f.content))
                except ConfigException as e:
                    raise ConfigException(e.message, 'src: {0}'.format(f.path))
                
                self.config['assets_url'] = absurl(self.config['assets_url'], '')
                self.config['base_url'] = absurl(self.opts.get('base_url', self.config['base_url']), '')
                
                for setting in ('archives_url', 'posts_url', 'tags_url'):
                    self.config[setting] = absurl(self.config[setting])
                
                for setting in ('archives_url', 'assets_url', 'base_url', 'posts_url', 'tags_url'):
                    if re.search(r'(?:^\.{2}/|/\.{2}$|/\.{2}/)', self.config[setting]):
                        raise ConfigException('Invalid config setting.', 'setting: {0}'.format(setting), 'path traversal is not allowed'.format(setting))
                
                for pattern in self.config['include']:
                    if op.commonprefix((self.src.path, normpath(self.src.path, pattern))) != self.src.path:
                        raise ConfigException('Invalid include path.', 'path: {0}'.format(pattern), 'path traversal is not allowed')
                
                break
        else:
            logger.debug('..  no config file found')
    
    
    def _parse(self):
        logger.info('>> Parsing')
        
        path = Directory(normpath(self.src.path, '_posts'))
        
        logger.debug('..  src: %s', path)
        
        for f in path:
            post = Post(f)
            
            content = self.parser.parse(self.renderer.from_string(post.bodymatter, post.frontmatter))
            excerpt = re.search(r'\A.*?(?:<p>(.+?)</p>)?', content, re.M | re.S).group(1)
            
            try:
                data = {
                    'content': content,
                    'date': post.date.strftime(self.config['date_format']).decode('utf-8'),
                    'excerpt': excerpt,
                    'tags': [],
                    'timestamp': timegm(post.date.utctimetuple()),
                    'url': self._get_post_url(post.date, post.slug)
                }
            except PageException:
                raise PageException('Invalid post slug.', 'src: {0}'.format(post.path))
            
            data.update(post.frontmatter)
            data['tags'].sort(key = unicode.lower)
            
            self.posts.append(data)
            
            for tag in data['tags']:
                if tag not in self.tags:
                    self.tags[tag] = []
                
                self.tags[tag].append(data)
    
    def _process(self):
        self._parse()
        
        logger.info('>> Processing')
        
        if self.posts:
            logger.debug('..  ordering posts')
            
            self.posts.sort(key = lambda post: post['timestamp'], reverse = True)
            
            logger.debug('..  generating archives')
            
            self.archives = self._archive(self.posts)
            
            logger.debug('..  sorting tags')
            
            tags = []
            
            for name, posts in self.tags:
                posts.sort(key = lambda post: post['timestamp'], reverse = True)
                
                try:
                    tags.append({
                        'archives': self._archive(posts),
                        'count': len(posts),
                        'name': name,
                        'posts': posts,
                        'url': self._get_tag_url(name)
                    })
                except PageException:
                    message = ['tag: {0}'.format(name)]
                    
                    for post in posts:
                        message.append('post: {0}'.format(post.get('title', post['url'])))
                    
                    raise PageException('Invalid tag slug.', *message)
            
            tags.sort(key = lambda tag: tag['name'].lower())
            tags.sort(key = lambda tag: tag['count'], reverse = True)
            
            self.tags.clear()
            
            for tag in tags:
                self.tags[tag['name']] = tag
        else:
            logger.debug('..  no posts found')
    
    def _render(self):
        self._process()
        
        logger.info('>> Rendering')
        
        self.renderer.register({
            'archives': self.archives,
            'posts': self.posts,
            'tags': self.tags
        })
        
        logger.debug('..  posts')
        
        for post in self.posts:
            try:
                self.pages.append(Page(
                    self._get_path(post['url']),
                    self._pygmentize(self.renderer.render(post['layout'], {'post': post}))
                ))
            except RendererException as e:
                raise RendererException(e.message, '{0} in post \'{1}\''.format(post['layout'], post['title']))
        
        logger.debug('..  pages')
        
        for f in self.src:
            if f.extension not in ('.html', '.htm', '.xml'):
                continue
            
            template = f.path.replace(self.src.path, '')
            
            self.pages.append(Page(
                normpath(self.dest.path, template),
                self._pygmentize(self.renderer.render(template))
            ))
        
        if self.config['tag_layout'] and self.tags:
            logger.debug('..  tags')
            
            for name, data in self.tags:
                self.pages.append(Page(
                    self._get_path(data['url']),
                    self._pygmentize(self.renderer.render(self.config['tag_layout'], {'tag': data}))
                ))
        
        if self.config['archive_layout'] and self.archives:
            logger.debug('..  archives')
            
            for year, data in self.archives:
                self.pages.append(Page(
                    self._get_path(data['url']),
                    self._pygmentize(self.renderer.render(self.config['archive_layout'], {'archive': data}))
                ))
    
    def _generate(self):
        logger.debug('>> Initializing\n..  src:  %s\n..  dest: %s', self.src.path, self.dest.path)
        
        self._update_config()
        
        self.renderer.register({'site': self.config})
        
        self._render()
        
        logger.info('>> Generating')
        
        assets_src = Directory(normpath(self.src.path, '_assets'))
        assets_dest = Directory(normpath(self.dest.path, *self.config['assets_url'].split('/')))
        
        if self.dest.exists:
            if self.opts['force']:
                self.dest.empty()
            else:
                self.dest.rm()
        else:
            self.dest.mk()
        
        for page in self.pages:
            page.mk()
        
        assets_src.cp(assets_dest.path)
        
        for pattern in self.config['include']:
            for path in iglob(normpath(self.src.path, pattern)):
                dest = path.replace(self.src.path, self.dest.path)
                
                if op.isdir(path):
                    Directory(path).cp(dest, False)
                elif op.isfile(path):
                    File(path).cp(dest)
        
        logger.info('Completed in %.3fs', time() - self._start)
    
    def _regenerate(self):
        logger.setLevel(logging.ERROR)
        
        self._parser = None
        self._renderer = None
        self._start = time()
        
        self.archives = OrderedDict()
        self.config = {}
        self.pages = []
        self.posts = []
        self.tags = OrderedDict()
        
        self._generate()
        
        logger.setLevel(getattr(logging, self.opts['level'], logging.INFO))
        logger.info('Regenerated in %.3fs', time() - self._start)
    
    
    def generate(self):
        self.src = Directory(self.opts['src'])
        self.dest = Directory(self.opts['dest'])
        
        if not self.src.exists:
            raise OptionException('Source must exist.')
        elif self.src == self.dest:
            raise OptionException('Source and destination must differ.')
        elif self.dest.exists and not (self.opts['force'] or self.opts['clean']):
            raise OptionException('Destination already exists.', 'the -c or -f flag must be passed to force generation by deleting or emptying the destination')
        
        self._generate()
    
    def init(self):
        self.src = Directory(self._get_theme(self.opts['theme']))
        self.dest = Directory(self.opts['dest'])
        
        if not self.src.exists:
            raise OptionException('Theme not found.')
        elif self.dest.exists and not self.opts['force']:
            raise OptionException('Destination already exists.', 'the -f flag must be passed to force initialization by deleting the destination')
        
        logger.info('>> Initializing')
        
        if self.opts['bare']:
            self.dest.rm()
            
            for d in ('_assets/css', '_assets/images', '_assets/js', '_templates', '_posts'):
                Directory(normpath(self.dest.path, d)).mk()
            
            File(normpath(self.dest.path, 'config.yml')).mk()
        else:
            self.src.cp(self.dest.path, False)
        
        logger.info('Completed in %.3fs', time() - self._start)
    
    def serve(self):
        self.src = Directory(self.opts['src'])
        base_url = absurl(self.opts['base_url'], '')
        
        if not self.src.exists:
            raise OptionException('Source must exist.')
        
        logger.info('>> Serving at 127.0.0.1:%s', self.opts['port'])
        logger.info('Press ctrl+c to stop.')
        
        cwd = getcwd()
        self.server = Server(('', self.opts['port']), base_url, RequestHandler)
        
        chdir(self.src.path)
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.server.shutdown()
            chdir(cwd)
            
            print('')
    
    def watch(self):
        self.src = Directory(self.opts['src'])
        self.dest = Directory(self.opts['dest'])
        
        if not self.src.exists:
            raise OptionException('Source must exist.')
        elif self.src == self.dest:
            raise OptionException('Source and destination must differ.')
        elif self.dest.exists and not self.opts['force']:
            raise OptionException('Destination already exists.', 'the -f flag must be passed to force watching by emptying the destination every time a change is made')
        
        logger.info('>> Watching')
        logger.info('Press ctrl+c to stop.')
        
        self.observer = Observer()
        
        self.observer.schedule(EventHandler(self.src.path, self._regenerate), self.src.path, True)
        self.observer.start()
        
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            
            print('')
        
        self.observer.join()
    
    
    @property
    def parser(self):
        if self._parser is None:
            self._parser = self._get_parser()(self.config.get(self.config['parser'], {}))
        
        return self._parser
    
    @property
    def renderer(self):
        if self._renderer is None:
            self._renderer = self._get_renderer()(self.src.path, self.config.get(self.config['renderer'], {}))
        
        return self._renderer

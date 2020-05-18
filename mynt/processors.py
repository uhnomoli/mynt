# -*- coding: utf-8 -*-

from calendar import timegm
from datetime import datetime
from importlib import import_module
from os import path as op
import re

from pkg_resources import DistributionNotFound
from pkg_resources import iter_entry_points, load_entry_point
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from mynt.containers import Configuration, Container, Item, Items, Posts
from mynt.exceptions import ConfigurationException, ContentException
from mynt.exceptions import ParserException, RendererException
from mynt.fs import File
from mynt.utils import get_logger, normpath, Timer, unescape, URL


logger = get_logger('mynt')


class Reader:
    def __init__(self, source, destination, site, writer):
        self._writer = writer

        self._parsers = {}
        self._extensions = {}
        self._cache = {}

        self.source = source
        self.destination = destination
        self.site = site

        self._find_parsers()


    def _find_parsers(self):
        for parser in iter_entry_points('mynt.parsers'):
            name = parser.name

            try:
                Parser = parser.load()
            except DistributionNotFound as error:
                logger.debug('@@ Parser could not be loaded: %s', name)
                logger.debug('..  %s', error)

                continue

            for extension in Parser.accepts:
                if extension in self._extensions:
                    self._extensions[extension].append(name)
                else:
                    self._extensions[extension] = [name]

            self._parsers[name] = Parser

        for parsers in self._extensions.values():
            parsers.sort(key=str.lower)

    def _get_date(self, mtime, date):
        if not date:
            return mtime

        d = [None, None, None, 0, 0]

        for i, v in enumerate(date.split('-')):
            d[i] = v

        if not d[3]:
            d[3], d[4] = mtime.strftime('%H %M').split()
        elif not d[4]:
            d[4] = '{0:02d}'.format(d[4])

        return datetime.strptime('-'.join(d), '%Y-%m-%d-%H-%M')

    def _get_parser(self, f, parser=None):
        if not parser:
            try:
                parser = self._extensions[f.extension][0]
            except KeyError:
                raise ParserException(
                    'Cannot find parser for file',
                    'src: {0}'.format(f.path))

        if parser in self._cache:
            return self._cache[parser]

        options = self.site.get(parser, None)

        if parser in self._parsers:
            Parser = self._parsers[parser](options)
        else:
            try:
                module = 'mynt.parsers.{0}'.format(parser)
                Parser = import_module(module).Parser(options)
            except ImportError:
                raise ParserException(
                    'Parser could not be imported: {0}'.format(parser))

        self._cache[parser] = Parser

        return Parser

    def _parse_filename(self, f):
        date, text = re.match(
            r'(?:(\d{4}(?:-\d{2}-\d{2}){1,2})-)?(.+)', f.name).groups()
        date = self._get_date(f.mtime, date)

        return (text, date)


    def _parse_container(self, container):
        for f in container.path:
            try:
                container.add(self._parse_item(container.configuration, f))
            except ParserException as error:
                logger.warn('@@ Error parsing file, skipping: %s', f.path)
                logger.debug(error)

        container.sort()
        container.tag()
        container.archive()

        return container

    def _parse_item(self, configuration, f, simple=False):
        Timer.start()

        item = Item(f.path)

        try:
            matches = re.search(
                r'\A---\s+^(.+?)$\s+---\s*(.*)\Z', f.content, re.M | re.S)
            frontmatter, bodymatter = matches.groups()
            frontmatter = Configuration(frontmatter)
        except AttributeError:
            raise ContentException('Invalid frontmatter',
                'src: {0}'.format(f.path),
                'frontmatter must not be empty')
        except ConfigurationException:
            raise ConfigurationException('Invalid frontmatter',
                'src: {0}'.format(f.path),
                'fontmatter contains invalid YAML')

        if 'layout' not in frontmatter:
            raise ContentException('Invalid frontmatter',
                'src: {0}'.format(f.path),
                'layout must be set')

        frontmatter.pop('url', None)

        parser = configuration.get('parser', None)
        parser = frontmatter.get('parser', parser)
        parser = self._get_parser(f, parser)

        text, date = self._parse_filename(f)
        content = self._writer.from_string(bodymatter, frontmatter)
        content = parser.parse(content)

        item['content'] = content
        item['date'] = date.strftime(self.site['date_format'])
        item['timestamp'] = timegm(date.utctimetuple())

        if simple:
            url = f.root.path.replace(self.source.path, '')

            item['url'] = URL.from_path(url, text)
        else:
            excerpt = re.search(
                r'\A.*?(?:<p>(.+?)</p>)?', content, re.M | re.S).group(1)
            url = URL.from_format(
                configuration['url'], text, date, frontmatter)

            item['excerpt'] = excerpt
            item['tags'] = []
            item['url'] = url

        item.update(frontmatter)

        logger.debug('..  (%.3fs) %s',
            Timer.stop(), f.path.replace(self.source.path, ''))

        return item


    def parse(self):
        posts = self._parse_container(Posts(self.source, self.site))
        containers = {}
        miscellany = Container('miscellany', self.source, None)
        pages = posts.pages

        for name, configuration in self.site['containers'].items():
            container = self._parse_container(Items(
                name, self.source, configuration))
            containers[name] = container
            pages.extend(container.pages)

        for f in miscellany.path:
            if f.extension in self._extensions:
                miscellany.add(self._parse_item(
                    miscellany.configuration, f, True))
            elif f.extension in ('.html', '.htm', '.xml'):
                pages.append((
                    f.path.replace(self.source.path, ''), None, None))

        pages.extend(miscellany.pages)

        return (posts, containers, pages)

class Writer:
    def __init__(self, source, destination, site):
        self.source = source
        self.destination = destination
        self.site = site

        self._renderer = self._get_renderer()


    def _get_path(self, url):
        parts = [self.destination.path] + url.split('/')

        if url.endswith('/'):
            parts.append('index.html')

        path = normpath(*parts)
        prefix = op.commonprefix((self.destination.path, path))

        if prefix != self.destination.path:
            raise ConfigurationException('Invalid URL',
                'url: {0}'.format(url),
                'path traversal is not allowed')

        return path

    def _get_renderer(self):
        renderer = self.site['renderer']
        options = self.site.get(renderer, None)

        try:
            Renderer = load_entry_point('mynt', 'mynt.renderers', renderer)
        except DistributionNotFound as error:
            raise RendererException(
                'Renderer could not be found: {0}'.format(renderer), error)
        except ImportError:
            try:
                module = 'mynt.renderers.{0}'.format(renderer)
                Renderer = import_module(module).Renderer
            except ImportError:
                raise RendererException(
                    'Renderer could not be imported: {0}'.format(renderer))

        return Renderer(self.source.path, options)

    def _highlight(self, match):
        language, code = match.groups()
        formatter = HtmlFormatter(linenos='table')
        code = unescape(code)

        try:
            code = highlight(code, get_lexer_by_name(language), formatter)
        except ClassNotFound:
            code = highlight(code, get_lexer_by_name('text'), formatter)

        return '<div class="code"><div>{0}</div></div>'.format(code)

    def _pygmentize(self, html):
        return re.sub(
            r'<pre><code[^>]+data-lang="([^>]+)"[^>]*>(.+?)</code></pre>',
            self._highlight, html, flags=re.S)


    def from_string(self, string, data=None):
        return self._renderer.from_string(string, data)

    def register(self, data):
        self._renderer.register(data)

    def render(self, template, data=None, url=None):
        url = url if url is not None else template
        path = self._get_path(url)

        try:
            Timer.start()

            content = self._renderer.render(template, data)

            if self.site['pygmentize']:
                content = self._pygmentize(content)

            logger.debug('..  (%.3fs) %s',
                Timer.stop(), path.replace(self.destination.path, ''))
        except RendererException as error:
            message = '{0} in container item {1}'.format(
                template, data.get('item', url))

            raise RendererException(error.message, message)

        return File(path, content)


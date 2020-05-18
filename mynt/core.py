# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from copy import deepcopy
from glob import iglob
from itertools import product
import locale
import logging
from os import chdir, getcwd, path as op
import re
from time import sleep

from pkg_resources import resource_filename
from watchdog.observers import Observer

from mynt import __version__
from mynt.containers import Configuration
from mynt.exceptions import ConfigurationException, OptionException
from mynt.fs import Directory, EventHandler, File
from mynt.processors import Reader, Writer
from mynt.server import RequestHandler, Server
from mynt.utils import get_logger, normpath, Timer, URL


logger = get_logger('mynt')


class Mynt:
    defaults = {
        'archive_layout': None,
        'archives_url': '/',
        'assets_url': '/assets/',
        'base_url': '/',
        'containers': {},
        'date_format': '%A, %B %d, %Y',
        'domain': None,
        'include': [],
        'locale': None,
        'posts_order': 'desc',
        'posts_sort': 'timestamp',
        'posts_url': '/<year>/<month>/<day>/<slug>/',
        'pygmentize': True,
        'renderer': 'jinja',
        'tag_layout': None,
        'tags_url': '/',
        'version': __version__}

    container_defaults = {
        'archive_layout': None,
        'archives_url': '/',
        'order': 'desc',
        'sort': 'timestamp',
        'tag_layout': None,
        'tags_url': '/'}


    def __init__(self, args=None):
        self._reader = None
        self._writer = None

        self.configuration = None
        self.posts = None
        self.containers = None
        self.data = {}
        self.pages = None

        self.options = self._get_options(args)

        logger.setLevel(getattr(
            logging, self.options['log_level'], logging.INFO))

        self.options['command']()


    def _generate(self):
        self._initialize()
        self._parse()
        self._render()

        logger.info('>> Generating')

        assets_source = Directory(normpath(self.source.path, '_assets'))
        assets_destination = self.configuration['assets_url'].split('/')
        assets_destination = Directory(normpath(
            self.destination.path, *assets_destination))

        if self.destination.exists:
            if self.options['force']:
                self.destination.empty()
            else:
                self.destination.rm()
        else:
            self.destination.mk()

        for page in self.pages:
            page.mk()

        assets_source.cp(assets_destination.path)

        for pattern in self.configuration['include']:
            for path in iglob(normpath(self.source.path, pattern)):
                destination = path.replace(
                    self.source.path, self.destination.path)

                if op.isdir(path):
                    Directory(path).cp(destination, False)
                elif op.isfile(path):
                    File(path).cp(destination)

    def _get_options(self, args):
        parser = ArgumentParser(
            description='A static site generator.')
        subparsers = parser.add_subparsers()

        parser.add_argument('-V', '--version',
            action='version', version='%(prog)s v{0}'.format(__version__),
            help="Prints %(prog)s's version and exits")

        log_level = parser.add_mutually_exclusive_group()
        log_level.add_argument('-l', '--log-level',
            default='INFO', type=str.upper,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help="Sets %(prog)s's log level")
        log_level.add_argument('-q', '--quiet',
            action='store_const', const='ERROR', dest='log_level',
            help="Sets %(prog)s's log level to ERROR")
        log_level.add_argument('-v', '--verbose',
            action='store_const', const='DEBUG', dest='log_level',
            help="Sets %(prog)s's log level to DEBUG")

        generate = subparsers.add_parser('generate',
            aliases=['gen', 'g'],
            help='Generates a static website')
        generate.add_argument('--base-url',
            default=self.defaults['base_url'],
            help='Overrides the base URL configuration option')
        generate.add_argument('--locale',
            default=self.defaults['locale'],
            help='Sets the renderer locale')
        generate.add_argument('source',
            nargs='?', default='.',
            help='Location of the %(prog)s website')
        generate.add_argument('destination',
            help='Location to output the generated static website')
        generate.set_defaults(command=self.generate)

        force=generate.add_mutually_exclusive_group()
        force.add_argument('-d', '--delete',
            action='store_true',
            help='Forces generation by DELETING the destination directory')
        force.add_argument('-f', '--force',
            action='store_true',
            help='Forces generation by EMPTYING the destination directory')

        initialize=subparsers.add_parser('initialize',
            aliases=['init', 'i'],
            help='Creates a new %(prog)s website')
        initialize.add_argument('--bare',
            action='store_true',
            help='Creates a new %(prog)s website without a theme')
        initialize.add_argument('-d', '--delete',
            action='store_true',
            help='Forces creation by DELETING the destination directory')
        initialize.add_argument('-t', '--theme',
            default='dark',
            help='Sets the %(prog)s website theme')
        initialize.add_argument('destination',
            help='Location to output the %(prog)s website')
        initialize.set_defaults(command=self.initialize)

        serve=subparsers.add_parser('serve',
            aliases=['s'],
            help='Starts a local server to host the static website')
        serve.add_argument('--base-url',
            default=self.defaults['base_url'],
            help='Overrides the base URL configuration option')
        serve.add_argument('-p', '--port',
            default=8080, type=int,
            help='Sets the port the server will listen on')
        serve.add_argument('source',
            nargs='?', default='.',
            help='Location of the static website')
        serve.set_defaults(command=self.serve)

        watch=subparsers.add_parser('watch',
            aliases=['w'],
            help='Regenerates a %(prog)s website when changes occur')
        watch.add_argument('--base-url',
            default=self.defaults['base_url'],
            help='Overrides the base URL configuration option')
        watch.add_argument('-f', '--force',
            action='store_true',
            help='Forces watching by EMPTYING the destination directory')
        watch.add_argument('--locale',
            default=self.defaults['locale'],
            help='Sets the renderer locale')
        watch.add_argument('source',
            nargs='?', default='.',
            help='Location of the %(prog)s website')
        watch.add_argument('destination',
            help='Location to output the generated static website')
        watch.set_defaults(command=self.watch)

        options = {}
        for name, value in vars(parser.parse_args(args)).items():
            if value is None:
                continue

            options[name] = value

        if 'command' not in options:
            raise OptionException(
                'Unknown command or option',
                parser.format_usage())

        return options

    def _get_theme(self, theme):
        return resource_filename(__name__, 'themes/{0}'.format(theme))

    def _initialize(self):
        logger.debug('>> Initializing')
        logger.debug('..  source: %s', self.source.path)
        logger.debug('..  destination: %s', self.destination.path)

        self._update_configuration()

        if self.configuration['locale']:
            try:
                locale.setlocale(locale.LC_ALL,
                    (self.configuration['locale'], 'utf-8'))
            except locale.Error:
                raise ConfigurationException(
                    'Locale not available',
                    'run `locale -a` to see available locales')

        self.writer.register({'site': self.configuration})

    def _parse(self):
        logger.info('>> Parsing')

        self.posts, self.containers, self.pages = self.reader.parse()

        self.data['posts'] = self.posts.data
        self.data['containers'] = {}

        for name, container in self.containers.items():
            self.data['containers'][name] = container.data

    def _regenerate(self):
        self._reader = None
        self._writer = None

        self.configuration = None
        self.posts = None
        self.containers = None
        self.data.clear()
        self.pages = None

        self._generate()

    def _render(self):
        logger.info('>> Rendering')

        self.writer.register(self.data)

        for i, page in enumerate(self.pages):
            self.pages[i] = self.writer.render(*page)

    def _update_configuration(self):
        self.configuration = deepcopy(self.defaults)

        logger.info('>> Searching for configuration file')

        for configuration in product(('mynt', 'config'), ('.yml', '.yaml')):
            configuration = ''.join(configuration)
            configuration = File(normpath(self.source.path, configuration))
            if not configuration.exists:
                continue

            logger.debug('..  found: %s', configuration.path)

            if configuration.name == 'config':
                logger.warn('@@ Deprecated configuration file found')
                logger.warn('..  rename config.yml to mynt.yml')

            break
        else:
            logger.debug('..  no configuration file found')

            return

        try:
            self.configuration.update(Configuration(configuration.content))
        except ConfigurationException as error:
            raise ConfigurationException(error.message,
                'source: {0}'.format(configuration.path))

        self.configuration['base_url'] = self.options.get('base_url')
        self.configuration['locale'] = self.options.get('locale')

        options = (
            'archives_url',
            'assets_url',
            'base_url',
            'posts_url',
            'tags_url')

        for option in options:
            url = URL.join(self.configuration[option], '')
            if re.search(r'(?:^\.{2}/|/\.{2}$|/\.{2}/)', url):
                raise ConfigurationException(
                    'Invalid configuration option',
                    'option: {0}'.format(self.configuration[option]),
                    'path traversal is not allowed')

        containers_source = normpath(self.source.path, '_containers')

        for name, options in self.configuration['containers'].items():
            prefix = op.commonprefix((
                containers_source, normpath(containers_source, name)))
            if prefix != containers_source:
                raise ConfigurationException(
                    'Invalid configuration option',
                    'setting: containers:{0}'.format(name),
                    'container name contains illegal characters')

            try:
                url = URL.join(options['url'])
            except KeyError:
                raise ConfigurationException(
                    'Invalid configuration option',
                    'setting: containers:{0}'.format(name),
                    'url must be set for all containers')

            if re.search(r'(?:^\.{2}/|/\.{2}$|/\.{2}/)', url):
                raise ConfigurationException(
                    'Invalid configuration option',
                    'setting: containers:{0}:url'.format(name),
                    'path traversal is not allowed')

            for name, value in self.container_defaults.items():
                if name not in options:
                    options[name] = value

            options['url'] = url

        for pattern in self.configuration['include']:
            prefix = op.commonprefix((
                self.source.path, normpath(self.source.path, pattern)))
            if prefix != self.source.path:
                raise ConfigurationException(
                    'Invalid include path',
                    'path: {0}'.format(pattern),
                    'path traversal is not allowed')


    def generate(self):
        Timer.start()

        self.source = Directory(self.options['source'])
        self.destination = Directory(self.options['destination'])

        if not self.source.exists:
            raise OptionException('Source must exist')
        elif self.source == self.destination:
            raise OptionException(
                'Source and destination must be different locations')
        elif self.destination.exists:
            if not (self.options['delete'] or self.options['force']):
                raise OptionException(
                    'Destination already exists',
                    'to force generation, use one of the following flags',
                    '  `-d` to DELETE the destination',
                    '  `-f` to EMPTY the destination')

        self._generate()

        logger.info('Completed in %.3fs', Timer.stop())

    def initialize(self):
        Timer.start()

        self.source = Directory(self._get_theme(self.options['theme']))
        self.destination = Directory(self.options['destination'])

        if not self.source.exists:
            raise OptionException('Theme not found')
        elif self.destination.exists and not self.options['delete']:
            raise OptionException(
                'Destination already exists',
                'to force initialization, use the following flag',
                '  `-d` to DELETE the destination')

        logger.info('>> Initializing')

        if self.options['bare']:
            self.destination.rm()

            directories = (
                '_assets/css',
                '_assets/images',
                '_assets/js',
                '_templates',
                '_posts')

            for d in directories:
                Directory(normpath(self.destination.path, d)).mk()

            File(normpath(self.destination.path, 'mynt.yml')).mk()
        else:
            self.source.cp(self.destination.path, False)

        logger.info('Completed in %.3fs', Timer.stop())

    def serve(self):
        self.source = Directory(self.options['source'])

        if not self.source.exists:
            raise OptionException('Source directory does not exist')

        logger.info('>> Serving at 127.0.0.1:%s', self.options['port'])
        logger.info('..  Press ctrl+c to stop')

        address = ('', self.options['port'])
        base_url = URL.join(self.options['base_url'], '')
        cwd = getcwd()

        chdir(self.source.path)

        try:
            self.server = Server(address, base_url, RequestHandler)
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.server.shutdown()
            chdir(cwd)

            print('')

    def watch(self):
        self.source = Directory(self.options['source'])
        self.destination = Directory(self.options['destination'])

        if not self.source.exists:
            raise OptionException('Source does not exist')
        elif self.source == self.destination:
            raise OptionException(
                'Source and destination must be different locations')
        elif self.destination.exists and not self.options['force']:
            raise OptionException(
                'Destination already exists',
                'to force generation, use the following flag',
                '  `-f` to EMPTY the destination')

        logger.info('>> Watching')
        logger.info('..  Press ctrl+c to stop')

        handler = EventHandler(self.source.path, self._regenerate)

        self.observer = Observer()
        self.observer.schedule(handler, self.source.path, True)
        self.observer.start()

        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()

            print('')

        self.observer.join()


    @property
    def reader(self):
        if self._reader is None:
            self._reader = Reader(
                self.source, self.destination, self.configuration, self.writer)

        return self._reader

    @property
    def writer(self):
        if self._writer is None:
            self._writer = Writer(
                self.source, self.destination, self.configuration)

        return self._writer


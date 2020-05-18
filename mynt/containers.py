# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime

import yaml

from mynt.exceptions import ConfigurationException
from mynt.fs import Directory
from mynt.utils import get_logger, normpath, URL


logger = get_logger('mynt')


class Configuration(dict):
    def __init__(self, string):
        super().__init__()

        try:
            self.update(yaml.safe_load(string))
        except yaml.YAMLError:
            raise ConfigurationException(
                'Configuration contains unsupported YAML')
        except:
            logger.debug('..  configuration file is empty')

            pass

class Data:
    def __init__(self, items, archives, tags):
        self.items = items
        self.archives = archives
        self.tags = tags


    def __iter__(self):
        return self.items.__iter__()

class Item(dict):
    def __init__(self, source, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__source = source


    def __str__(self):
        return self.__source

class Tag:
    def __init__(self, name, url, count, items, archives):
        self.name = name
        self.url = url
        self.count = count
        self.items = items
        self.archives = archives


    def __iter__(self):
        return self.items.__iter__()


class Container:
    def __init__(self, name, source, configuration):
        self._pages = None

        self.name = name
        self.path = source
        self.configuration = {} if configuration is None else configuration
        self.data = Data([], OrderedDict(), OrderedDict())


    def _get_pages(self):
        pages = []

        for item in self.items:
            if item['layout'] is None:
                continue

            pages.append((item['layout'], {'item': item}, item['url']))

        return pages


    def add(self, item):
        self.items.append(item)

    def archive(self):
        pass

    def sort(self):
        pass

    def tag(self):
        pass


    @property
    def archives(self):
        return self.data.archives

    @property
    def items(self):
        return self.data.items

    @property
    def pages(self):
        if self._pages is None:
            self._pages = self._get_pages()

        return self._pages

    @property
    def tags(self):
        return self.data.tags


class Items(Container):
    _sort_order = {
        'asc': False,
        'desc': True}


    def __init__(self, name, source, configuration):
        super().__init__(name, source, configuration)

        self.path = Directory(normpath(source.path, '_containers', self.name))


    def _archive(self, items, archive):
        for item in items:
            timestamp = datetime.utcfromtimestamp(item['timestamp'])
            year, month = timestamp.strftime('%Y %B').split()

            if year not in archive:
                months = OrderedDict({month: [item]})
                url = URL.from_format(self.configuration['archives_url'], year)

                archive[year] = {'months': months, 'url': url, 'year': year}
            elif month not in archive[year]['months']:
                archive[year]['months'][month] = [item]
            else:
                archive[year]['months'][month].append(item)

    def _get_pages(self):
        pages = super()._get_pages()

        if self.configuration['archive_layout'] and self.archives:
            for archive in self.archives.values():
                pages.append((
                    self.configuration['archive_layout'],
                    {'archive': archive},
                    archive['url']))

        if self.configuration['tag_layout'] and self.tags:
            for tag in self.tags.values():
                pages.append((
                    self.configuration['tag_layout'],
                    {'tag': tag},
                    tag.url))

        return pages

    def _relate(self):
        for i, item in enumerate(self.items):
            if i:
                item['prev'] = self.items[i-1]
            else:
                item['prev'] = None

            try:
                item['next'] = self.items[i+1]
            except IndexError:
                item['next'] = None

    def _sort(self, container, key, order='asc'):
        reverse = self._sort_order.get(order.lower(), False)

        def sort(item):
            try:
                attribute = item.get(key, item)
            except AttributeError:
                attribute = getattr(item, key, item)

            if isinstance(attribute, str):
                return attribute.lower()

            return attribute

        container.sort(key=sort, reverse=reverse)


    def archive(self):
        self._archive(self.items, self.archives)

        for tag in self.tags.values():
            self._archive(tag.items, tag.archives)

    def sort(self):
        key = self.configuration['sort']
        order = self.configuration['order']

        self._sort(self.items, key, order)
        self._relate()

    def tag(self):
        tags = []

        for item in self.items:
            item['tags'].sort(key=str.lower)

            for tag in item['tags']:
                if tag not in self.tags:
                    self.tags[tag] = []

                self.tags[tag].append(item)

        for name, items in self.tags.items():
            url = URL.from_format(self.configuration['tags_url'], name)

            tags.append(Tag(name, url, len(items), items, OrderedDict()))

        self._sort(tags, 'name')
        self._sort(tags, 'count', 'desc')

        self.tags.clear()

        for tag in tags:
            self.tags[tag.name] = tag


class Posts(Items):
    def __init__(self, source, site):
        super().__init__('posts', source, self._get_configuration(site))

        self.path = Directory(normpath(source.path, '_posts'))


    def _get_configuration(self, site):
        configuration = {
            'archives_url': 'archives_url',
            'archive_layout': 'archive_layout',
            'order': 'posts_order',
            'sort': 'posts_sort',
            'tags_url': 'tags_url',
            'tag_layout': 'tag_layout',
            'url': 'posts_url'}

        for name, value in configuration.items():
            configuration[name] = site.get(value)

        return configuration


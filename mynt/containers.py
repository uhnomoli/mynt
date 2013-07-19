# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime

import yaml

from mynt.exceptions import ConfigException
from mynt.fs import Directory
from mynt.utils import absurl, Data, format_url, get_logger, normpath, slugify


yaml.add_constructor('tag:yaml.org,2002:str', lambda loader, node: loader.construct_scalar(node))

logger = get_logger('mynt')


class Config(dict):
    def __init__(self, string):
        super(Config, self).__init__()
        
        try:
            self.update(yaml.load(string))
        except yaml.YAMLError:
            raise ConfigException('Config contains unsupported YAML.')
        except:
            logger.debug('..  config file is empty')
            
            pass


class Container(object):
    def __init__(self, name, src, config):
        self._pages = None
        
        self.name = name
        self.src = src
        self.path = Directory(normpath(self.src.path, '_containers', self.name))
        self.config = config
        self.data = Data([], OrderedDict(), OrderedDict())
    
    
    def _archive(self, container, archive):
        for item in container:
            year, month = datetime.utcfromtimestamp(item['timestamp']).strftime('%Y %B').decode('utf-8').split()
            
            if year not in archive:
                archive[year] = {
                    'months': OrderedDict({month: [item]}),
                    'url': self._get_page_url(self.config['archives_url'], year),
                    'year': year
                }
            elif month not in archive[year]['months']:
                archive[year]['months'][month] = [item]
            else:
                archive[year]['months'][month].append(item)
    
    def _get_page_url(self, url, text):
        slug = slugify(text)
        
        return format_url(absurl(url, slug), url.endswith('/'))
    
    def _get_pages(self):
        pages = []
        
        for item in self.container:
            pages.append((item['layout'], {'item': item}, item['url']))
        
        if self.config['archive_layout'] and self.archives:
            for archive in self.archives.itervalues():
                pages.append((
                    self.config['archive_layout'],
                    {'archive': archive},
                    archive['url']
                ))
        
        if self.config['tag_layout'] and self.tags:
            for tag in self.tags.itervalues():
                pages.append((
                    self.config['tag_layout'],
                    {'tag': tag},
                    tag['url']
                ))
        
        return pages
    
    def _relate(self):
        for index, item in enumerate(self.container):
            if index:
                item['prev'] = self.container[index - 1]
            else:
                item['prev'] = None
            
            try:
                item['next'] = self.container[index + 1]
            except IndexError:
                item['next'] = None
    
    def _sort(self, container, key, reverse = False):
        def sort(item):
            attribute = item.get(key, item)
            
            if isinstance(attribute, basestring):
                return attribute.lower()
            
            return attribute
        
        container.sort(key = sort, reverse = reverse)
    
    
    def add(self, item):
        self.container.append(item)
    
    def archive(self):
        self._archive(self.container, self.archives)
        
        for tag in self.tags.itervalues():
            self._archive(tag['container'], tag['archives'])
    
    def sort(self):
        self._sort(self.container, self.config['sort'], self.config['reverse'])
        self._relate()
    
    def tag(self):
        tags = []
        
        for item in self.container:
            item['tags'].sort(key = unicode.lower)
            
            for tag in item['tags']:
                if tag not in self.tags:
                    self.tags[tag] = []
                
                self.tags[tag].append(item)
        
        for name, container in self.tags.iteritems():
            tags.append({
                'archives': OrderedDict(),
                'count': len(container),
                'name': name,
                'container': container,
                'url': self._get_page_url(self.config['tags_url'], name)
            })
        
        self._sort(tags, 'name')
        self._sort(tags, 'count', True)
        
        self.tags.clear()
        
        for tag in tags:
            self.tags[tag['name']] = tag
    
    
    @property
    def archives(self):
        return self.data.archives
    
    @property
    def container(self):
        return self.data.container
    
    @property
    def pages(self):
        if self._pages is None:
            self._pages = self._get_pages()
        
        return self._pages
    
    @property
    def tags(self):
        return self.data.tags


class Posts(Container):
    def __init__(self, src, config):
        super(Posts, self).__init__('posts', src, config)
        
        self.path = Directory(normpath(self.src.path, '_posts'))
        
        self._update_config()
    
    
    def _update_config(self):
        config = {
            'archives_url': 'archives_url',
            'archive_layout': 'archive_layout',
            'reverse': True,
            'sort': 'timestamp',
            'tags_url': 'tags_url',
            'tag_layout': 'tag_layout',
            'url': 'posts_url'
        }
        
        for k, v in config.iteritems():
            config[k] = self.config.get(v, v)
        
        self.config = config

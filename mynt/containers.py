# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime
import re

import yaml

from mynt.exceptions import ConfigException, PostException
from mynt.fs import File
from mynt.utils import get_logger


yaml.add_constructor('tag:yaml.org,2002:str', lambda loader, node: loader.construct_scalar(node))

logger = get_logger('mynt')


class Archives(object):
    posts = OrderedDict()
    
    
    def __init__(self, posts):
        for post in posts:
            year, month = datetime.utcfromtimestamp(post['timestamp']).strftime('%Y %B').split()
            
            if year not in self.posts:
                self.posts[year] = OrderedDict({month: [post]})
            elif month not in self.posts[year]:
                self.posts[year][month] = [post]
            else:
                self.posts[year][month].append(post)
    
    
    def __iter__(self):
        for year, months in self.posts.iteritems():
            yield (year, months.items())

class Config(dict):
    def __init__(self, string):
        super(Config, self).__init__()
        
        try:
            self.update(yaml.load(string))
        except yaml.YAMLError:
            raise ConfigException('Config contains unsupported YAML.')
        except:
            raise ConfigException('Invalid config format.')

class Page(File):
    pass

class Post(object):
    def __init__(self, post):
        self.path = post.path
        self.root = post.root
        self.name = post.name
        self.extension = post.extension
        
        logger.debug('..  {0}.{1}'.format(self.name, self.extension))
        
        try:
            date, self.slug = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', self.name).groups()
            self.date = datetime.strptime(date, '%Y-%m-%d')
        except (AttributeError, ValueError):
            raise PostException('Invalid post filename.', 'src: {0}'.format(self.path), 'must be of the format \'YYYY-MM-DD-Post-title.md\'')
        
        try:
            frontmatter, self.bodymatter = re.search(r'\A---\s+^(.+?)$\s+---\s*(.*)\Z', post.content, re.M | re.S).groups()
        except AttributeError:
            raise PostException('Invalid post format.', 'src: {0}'.format(self.path), 'frontmatter must not be empty')
        
        try:
            self.frontmatter = Config(frontmatter)
        except ConfigException as e:
            raise ConfigException('Invalid post frontmatter.', 'src: {0}'.format(self.path), e.message.lower().replace('.', ''))
        
        if 'layout' not in self.frontmatter:
            raise PostException('Invalid post frontmatter.', 'src: {0}'.format(self.path), 'layout must be set')

class Tags(OrderedDict):
    def __iter__(self):
        for name in super(Tags, self).__iter__():
            yield (name, self[name])

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime
import re

import yaml

from mynt.exceptions import ConfigException, PostException
from mynt.fs import File
from mynt.utils import get_logger


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
            date, self.slug = re.match(r'(\d{4}(?:-\d{2}-\d{2}){1,2})-(.+)', self.name).groups()
            self.date = self._get_date(post.mtime, date)
        except (AttributeError, ValueError):
            raise PostException('Invalid post filename.', 'src: {0}'.format(self.path), 'must be of the format \'YYYY-MM-DD[-HH-MM]-Post-title.md\'')
        
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
    
    
    def _get_date(self, mtime, date):
        d = [None, None, None, 0, 0]
        
        for i, v in enumerate(date.split('-')):
            d[i] = v
        
        if not d[3]:
            d[3], d[4] = mtime.strftime('%H %M').decode('utf-8').split()
        elif not d[4]:
            d[4] = '{0:02d}'.format(d[4])
        
        return datetime.strptime('-'.join(d), '%Y-%m-%d-%H-%M')

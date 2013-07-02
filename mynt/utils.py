# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from os import path as op
import re
from time import time


def _cleanpath(*args):
    parts = [args[0].strip()]
    
    for arg in args[1:]:
        parts.append(arg.strip(' \t\n\r\v\f' + op.sep))
    
    return parts


def abspath(*args):
    return op.realpath(
        op.expanduser(
            op.join(
                *_cleanpath(*args)
            )
        )
    )

def absurl(*args):
    url = '/'.join(args)
    
    if not re.match(r'[^/]+://', url):
        url = '/' + url
    
    return re.sub(r'(?<!:)//+', '/', url)

def get_logger(name):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        
        logger.addHandler(handler)
    
    return logger

def normpath(*args):
    return op.normpath(
        op.join(
            *_cleanpath(*args)
        )
    )

def slugify(string):
    slug = re.sub(r'\s+', '-', string.strip())
    slug = re.sub(r'[^a-z0-9\-_.]', '', slug, flags = re.I)
    
    return slug


def format_url(url, clean):
    if clean:
        return absurl(url, '')
    
    return '{0}.html'.format(url)


class Data(object):
    def __init__(self, container, archives, tags):
        self.container = container
        self.archives = archives
        self.tags = tags
    
    
    def __iter__(self):
        return self.container.__iter__()

class Item(dict):
    def __init__(self, src, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        
        self.__src = src
    
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.__src

class Timer(object):
    _start = []
    
    
    @classmethod
    def start(cls):
        cls._start.append(time())
    
    @classmethod
    def stop(cls):
        return time() - cls._start.pop()

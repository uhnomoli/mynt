# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict as _OrderedDict
from xml.sax.saxutils import escape, unescape
import logging
from os import path as op
from re import match, sub


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
    
    if not match(r'[^/]+://', url):
        url = '/' + url
    
    return sub(r'(?<!:)//+', '/', url)

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


class OrderedDict(_OrderedDict):
    def __iter__(self):
        for key in super(OrderedDict, self).__iter__():
            yield (key, self[key])


_html_escape_table = {
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;"
}


_html_unescape_table = {v: k for k, v in _html_escape_table.iteritems()}


def escape_html(text):
    return escape(text, _html_escape_table)


def unescape_html(text):
    return unescape(text, _html_unescape_table)

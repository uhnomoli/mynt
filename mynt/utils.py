# -*- coding: utf-8 -*-

import logging
from os import path as op
import re
from time import time


_ENTITIES = [
    ('&', ['&amp;', '&#x26;', '&#38;']),
    ('<', ['&lt;', '&#x3C;', '&#60;']),
    ('>', ['&gt;', '&#x3E;', '&#62;']),
    ('"', ['&quot;', '&#x22;', '&#34;']),
    ("'", ['&#x27;', '&#39;']),
    ('/', ['&#x2F;', '&#47;'])]


def _cleanpath(*args):
    characters = '\f\n\r\t\v {0}'.format(op.sep)
    parts = [args[0].strip()]

    for arg in args[1:]:
        parts.append(arg.strip(characters))

    return parts


def abspath(*args):
    path = _cleanpath(*args)
    path = op.join(*path)
    path = op.expanduser(path)

    return op.realpath(path)

def escape(html):
    for match, replacements in _ENTITIES:
        html = html.replace(match, replacements[0])

    return html

def get_logger(name):
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()

        logger.addHandler(handler)

    return logger

def normpath(*args):
    path = _cleanpath(*args)
    path = op.join(*path)

    return op.normpath(path)

def unescape(html):
    for replace, matches in _ENTITIES:
        for match in matches:
            html = html.replace(match, replace)

    return html


class Timer:
    _start = []


    @classmethod
    def start(cls):
        cls._start.append(time())

    @classmethod
    def stop(cls):
        return time() - cls._start.pop()

class URL:
    @staticmethod
    def join(*args):
        url = '/'.join(args)

        if not re.match(r'[^/]+://', url):
            url = '/' + url

        return re.sub(r'(?<!:)//+', '/', url)

    @staticmethod
    def slugify(string):
        slug = re.sub(r'\s+', '-', string.strip())
        slug = re.sub(r'[^a-z0-9\-_.]', '', slug, flags=re.I)

        return slug


    @classmethod
    def format(cls, url, clean):
        if clean:
            return cls.join(url, '')

        return '{0}.html'.format(url)

    @classmethod
    def from_format(cls, url, string, date=None, data=None):
        clean = url.endswith('/')
        slug = cls.slugify(string)

        if '<slug>' in url:
            url = url.replace('<slug>', slug)
        else:
            url = cls.join(url, slug)

        if date is not None:
            subs = {
                '<year>': '%Y',
                '<month>': '%m',
                '<day>': '%d',
                '<i_month>': str(date.month),
                '<i_day>': str(date.day)}

            url = url.replace('%', '%%')

            for match, replace in subs.items():
                url = url.replace(match, replace)

            url = date.strftime(url)

        if data is not None:
            for attribute, value in data.items():
                if isinstance(value, str):
                    match = '<{0}>'.format(attribute)
                    url = url.replace(match, cls.slugify(value))

        if clean:
            return cls.join(url, '')

        return '{0}.html'.format(url)

    @classmethod
    def from_path(cls, root, string):
        name = '{0}.html'.format(cls.slugify(string))

        return normpath(root, name)


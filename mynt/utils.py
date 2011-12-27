# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict as _OrderedDict
import logging
from os import path as op
from re import match, sub


def _cleanpath(*args):
    parts = [args[0].strip()]
    
    for arg in args[1:]:
        parts.append((arg.replace(op.sep, '', 1) if arg.startswith(op.sep) else arg).strip())
    
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
    if match('.+://', args[0]):
        return sub(r'(?<!:)//+', '/', '/'.join(args))
    else:
        return sub(r'//+', '/', '/' + '/'.join(args))

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

# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class Parser(object):
    def __init__(self, options):
        self.options = options
        
        self.setup()
    
    
    def parse(self, content):
        raise NotImplementedError('A parser must implement parse.')
    
    def setup(self):
        pass

class Renderer(object):
    def __init__(self, path, options, globals_ = {}):
        self.path = path
        self.options = options
        self.globals = globals_
        
        self.setup()
    
    
    def from_string(self, source, vars_ = {}):
        raise NotImplementedError('A renderer must implement from_string.')
    
    def register(self, key, value):
        raise NotImplementedError('A renderer must implement register.')
    
    def render(self, template, vars_ = {}):
        raise NotImplementedError('A renderer must implement render.')
    
    def setup(self):
        pass

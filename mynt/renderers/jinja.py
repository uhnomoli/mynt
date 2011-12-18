# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime
from math import ceil

from jinja2 import Environment, FileSystemLoader, PrefixLoader
from jinja2.exceptions import TemplateNotFound

from mynt.base import Renderer as _Renderer
from mynt.exceptions import RendererException
from mynt.utils import absurl, normpath


class _PrefixLoader(PrefixLoader):
    def get_source(self, environment, template):
        try:
            if not self.delimiter:
                for prefix in self.mapping:
                    if template.startswith(prefix):
                        name = template.replace(prefix, '', 1)
                        loader = self.mapping[prefix]
                        
                        break
                else:
                    raise TemplateNotFound(template)
            else:
                prefix, name = template.split(self.delimiter, 1)
                loader = self.mapping[prefix]
        except (KeyError, ValueError):
            raise TemplateNotFound(template)
        
        try:
            return loader.get_source(environment, name)
        except TemplateNotFound:
            raise TemplateNotFound(template)


class Renderer(_Renderer):
    config = {}
    
    
    def _date(self, ts, format = '%A, %B %d, %Y'):
        if ts is None:
            return datetime.utcnow().strftime(format).decode('utf-8')
        
        return datetime.utcfromtimestamp(ts).strftime(format).decode('utf-8')
    
    def _get_asset(self, asset):
        return absurl(self.globals['site']['base_url'], self.globals['site']['assets_url'], asset)
    
    def _get_url(self, url = ''):
        return absurl(self.globals['site']['base_url'], url)
    
    def _needed(self, iterable, multiple):
        length = float(len(iterable))
        multiple = float(multiple)
        
        return int((ceil(length / multiple) * multiple) - length)
    
    
    def from_string(self, source, vars_ = {}):
        template = self.environment.from_string(source)
        
        return template.render(**vars_)
    
    def register(self, vars_):
        self.globals.update(vars_)
        self.environment.globals.update(vars_)
    
    def render(self, template, vars_ = {}):
        try:
            template = self.environment.get_template(template)
        except TemplateNotFound:
            raise RendererException('Template not found.')
        
        return template.render(**vars_)
    
    def setup(self):
        self.config.update(self.options)
        self.config['loader'] = _PrefixLoader(OrderedDict([
            ('/', FileSystemLoader(self.path)),
            ('', FileSystemLoader(normpath(self.path, '_templates')))
        ]), None)
        
        self.environment = Environment(**self.config)
        
        self.environment.filters['date'] = self._date
        self.environment.filters['needed'] = self._needed
        
        self.environment.globals.update(self.globals)
        self.environment.globals['get_asset'] = self._get_asset
        self.environment.globals['get_url'] = self._get_url

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime
from os import path as op
from re import sub

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
        
        # Gross hack to appease Jinja when handling Windows paths.
        if op.sep != '/':
            name = name.replace(op.sep, '/')
        
        try:
            return loader.get_source(environment, name)
        except TemplateNotFound:
            raise TemplateNotFound(template)


class Renderer(_Renderer):
    config = {}
    
    
    def _absolutize(self, html):
        def _replace(match):
            return self._get_url(match.group(1).replace(self.globals['site']['base_url'], ''), True)
        
        return sub(r'(?<==")(/[^"]*)', _replace, html)
    
    def _date(self, ts, format = '%A, %B %d, %Y'):
        if ts is None:
            return datetime.utcnow().strftime(format).decode('utf-8')
        
        return datetime.utcfromtimestamp(ts).strftime(format).decode('utf-8')
    
    def _get_asset(self, asset):
        return absurl(self.globals['site']['base_url'], self.globals['site']['assets_url'], asset)
    
    def _get_url(self, url = '', absolute = False):
        domain = self.globals['site']['domain']
        
        if not absolute or not domain:
            domain = ''
        elif not domain.startswith(('http://', 'https://')):
            domain = 'http://' + domain
        
        return absurl(domain, self.globals['site']['base_url'], url)
    
    
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
            (op.sep, FileSystemLoader(self.path)),
            ('', FileSystemLoader(normpath(self.path, '_templates')))
        ]), None)
        
        self.environment = Environment(**self.config)
        
        self.environment.filters['absolutize'] = self._absolutize
        self.environment.filters['date'] = self._date
        
        self.environment.globals.update(self.globals)
        self.environment.globals['get_asset'] = self._get_asset
        self.environment.globals['get_url'] = self._get_url

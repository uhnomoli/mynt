# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
import gettext
import locale
from os import path as op
import re

from jinja2 import Environment, FileSystemLoader, PrefixLoader
from jinja2.exceptions import TemplateNotFound

from mynt.base import Renderer as _Renderer
from mynt.exceptions import RendererException
from mynt.utils import normpath, URL


class _PrefixLoader(PrefixLoader):
    def get_loader(self, template):
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

        return (loader, name)


class Renderer(_Renderer):
    configuration = {}


    def _absolutize(self, html):
        base_url = self.globals['site']['base_url']

        def _replace(match):
            return self._get_url(match.group(1).replace(base_url, '', 1))

        return re.sub(r'(?<==")({0}[^"]*)'.format(base_url), _replace, html)

    def _date(self, ts, date='%A, %B %d, %Y'):
        if ts is None:
            return datetime.utcnow().strftime(date)

        return datetime.utcfromtimestamp(ts).strftime(date)

    def _get_asset(self, asset):
        assets_url = self.globals['site']['assets_url']
        base_url = self.globals['site']['base_url']

        return URL.join(base_url, assets_url, asset)

    def _get_url(self, url='', absolute=False):
        parts = [self.globals['site']['base_url'], url]
        domain = self.globals['site']['domain']

        if absolute and domain:
            parts.insert(0, domain)

        return URL.join(*parts)

    def _items(self, dictionary):
        return dictionary.items()

    def _values(self, dictionary):
        return dictionary.values()


    def from_string(self, string, data=None):
        data = data if data is not None else {}

        template = self.environment.from_string(string)

        return template.render(**data)

    def register(self, data):
        self.globals.update(data)
        self.environment.globals.update(data)

    def render(self, template, data=None):
        data = data if data is not None else {}

        try:
            template = self.environment.get_template(template)
        except TemplateNotFound:
            raise RendererException('Template not found')

        return template.render(**data)

    def setup(self):
        self.configuration.update(self.options)
        self.configuration['loader'] = _PrefixLoader(OrderedDict([
            (op.sep, FileSystemLoader(self.path)),
            ('', FileSystemLoader(normpath(self.path, '_templates')))
        ]), None)

        self.environment = Environment(**self.configuration)

        self.environment.filters['absolutize'] = self._absolutize
        self.environment.filters['date'] = self._date
        self.environment.filters['items'] = self._items
        self.environment.filters['values'] = self._values

        self.environment.globals.update(self.globals)
        self.environment.globals['get_asset'] = self._get_asset
        self.environment.globals['get_url'] = self._get_url

        if 'extensions' in self.configuration:
            if 'jinja2.ext.i18n' in self.configuration['extensions']:
                try:
                    locales = [locale.getlocale(locale.LC_MESSAGES)[0]]
                except AttributeError:
                    locales = None

                translation = gettext.translation(
                    gettext.textdomain(),
                    normpath(self.path, '_locales'),
                    locales,
                    fallback=True)

                self.environment.install_gettext_translation(translation)


# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import re

import misaka as m

from mynt.base import Parser as _Parser


class _Renderer(m.HtmlRenderer):
    _toc_ids = {}
    _toc_patterns = [
        (r'<[^<]+?>', ''),
        (r'[^a-z0-9_.\s-]', ''),
        (r'\s+', '-'),
        (r'^[^a-z]+', ''),
        (r'^$', 'section')
    ]
    
    def block_code(self, text, lang):
        lang = ' lang="{0}"'.format(lang) if lang else ''
        
        return '<pre{0}><code>{1}</code></pre>'.format(lang, text)
    
    def header(self, text, level):
        if self.flags & m.HTML_TOC:
            identifier = text.lower()
            
            for pattern, replace in self._toc_patterns:
                identifier = re.sub(pattern, replace, identifier)
            
            if identifier in self._toc_ids:
                self._toc_ids[identifier] += 1
                identifier = '{0}-{1}'.format(identifier, self._toc_ids[identifier])
            else:
                self._toc_ids[identifier] = 1
            
            return '<h{0} id="{1}">{2}</h{0}>'.format(level, identifier, text)
        else:
            return '<h{0}>{1}</h{0}>'.format(level, text)


class Parser(_Parser):
    lookup = {
        'extensions': {
            'autolink': m.EXT_AUTOLINK,
            'fenced_code': m.EXT_FENCED_CODE,
            'lax_html_blocks': m.EXT_LAX_HTML_BLOCKS,
            'no_intra_emphasis': m.EXT_NO_INTRA_EMPHASIS,
            'space_headers': m.EXT_SPACE_HEADERS,
            'strikethrough': m.EXT_STRIKETHROUGH,
            'superscript': m.EXT_SUPERSCRIPT,
            'tables': m.EXT_TABLES
        },
        'render_flags': {
            'expand_tabs': m.HTML_EXPAND_TABS,
            'hard_wrap': m.HTML_HARD_WRAP,
            'safelink': m.HTML_SAFELINK,
            'skip_html': m.HTML_SKIP_HTML,
            'skip_images': m.HTML_SKIP_IMAGES,
            'skip_links': m.HTML_SKIP_LINKS,
            'skip_style': m.HTML_SKIP_STYLE,
            'smartypants': m.HTML_SMARTYPANTS,
            'toc': m.HTML_TOC,
            'toc_tree': m.HTML_TOC_TREE,
            'use_xhtml': m.HTML_USE_XHTML
        }
    }
    
    config = {
        'extensions': {
            'autolink': True,
            'fenced_code': True,
            'no_intra_emphasis': True,
            'strikethrough': True
        },
        'render_flags': {
            'hard_wrap': True,
            'smartypants': True
        }
    }
    
    flags = {
        'extensions': 0,
        'render_flags': 0
    }
    
    
    def parse(self, markdown):
        return self._html.render(markdown)
    
    def setup(self):
        for k, v in self.options.iteritems():
            self.config[k].update(v)
        
        for group, options in self.config.iteritems():
            for option, value in options.iteritems():
                if value:
                    self.flags[group] |= self.lookup[group][option]
        
        self._html = m.Markdown(_Renderer(self.flags['render_flags']), self.flags['extensions'])

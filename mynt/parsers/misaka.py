# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from copy import deepcopy
from operator import or_
import re

import houdini as h
import misaka as m

from mynt.base import Parser as _Parser


class _Renderer(m.HtmlRenderer):
    _toc_patterns = [
        (r'<[^<]+?>', ''),
        (r'[^a-z0-9_.\s-]', ''),
        (r'\s+', '-'),
        (r'^[^a-z]+', ''),
        (r'^$', 'section')
    ]
    
    
    def block_code(self, text, lang):
        text = h.escape_html(text.encode('utf-8'), 1).decode('utf-8')
        lang = ' data-lang="{0}"'.format(lang) if lang else ''
        
        return '<pre><code{0}>{1}</code></pre>'.format(lang, text)
    
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
    
    
    def setup(self):
        super(_Renderer, self).setup()
        
        self._sp = m.SmartyPants().postprocess
        self._toc_ids = {}
    
    def preprocess(self, markdown):
        self._toc_ids.clear()
        
        return markdown
    
    def postprocess(self, html):
        if self.flags & m.HTML_SMARTYPANTS:
            html = self._sp(html)
        
        return html


class Parser(_Parser):
    accepts = ('.md',)
    
    
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
    
    defaults = {
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
    
    
    def parse(self, markdown):
        return self._html.render(markdown)
    
    def setup(self):
        self.flags = {}
        self.config = deepcopy(self.defaults)
        
        for k, v in self.options.iteritems():
            self.config[k].update(v)
        
        for group, options in self.config.iteritems():
            flags = [self.lookup[group][k] for k, v in options.iteritems() if v]
            
            self.flags[group] = reduce(or_, flags, 0)
        
        self._html = m.Markdown(_Renderer(self.flags['render_flags']), self.flags['extensions'])

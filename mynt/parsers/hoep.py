# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from copy import deepcopy
from operator import or_
import re

import hoep as h

from mynt.base import Parser as _Parser
from mynt.utils import escape


class _TOCLeaf:

    def __init__(self, hlevel = 0, identifier = None, text = None):
        self.level = 0
        self.parent = None
        self.children = []
        self.hlevel = hlevel
        self.identifier = identifier
        self.text = text


class _Renderer(h.Hoep):
    def __init__(self, extensions = 0, render_flags = 0):
        super(_Renderer, self).__init__(extensions, render_flags)

        if self.render_flags & h.HTML_TOC:
            self._toc_ids = {}
            self._toc_patterns = (
                (r'<[^<]+?>', ''),
                (r'[^a-z0-9_.\s-]', ''),
                (r'\s+', '-'),
                (r'^[^a-z]+', ''),
                (r'^$', 'section')
            )
    
    
    def block_code(self, text, language):
        text = escape(text)
        language = ' data-lang="{0}"'.format(language) if language else ''
        
        return '<pre><code{0}>{1}</code></pre>'.format(language, text)
    
    def footnotes(self, text):
        return '<div class="footnotes"><ol>{0}</ol></div>'.format(text)
    
    def footnote_def(self, text, number):
        link = '&nbsp;<a href="#fnref{0}" rev="footnote">↩</a>'.format(number)
        index = text.rfind('</p>')
        
        if index:
            text = ''.join((text[:index], link, text[index:]))
        else:
            text = ''.join((text, link))
        
        return '<li id="fn{0}" class="footnotes-def">{1}</li>'.format(number, text)
    
    def footnote_ref(self, number):
        return '<sup id="fnref{0}" class="footnotes-ref"><a href="#fn{0}" rel="footnote">{0}</a></sup>'.format(number)
    
    def header(self, text, hlevel):
        if self.render_flags & h.HTML_TOC:
            identifier = text.lower()
            
            for pattern, replace in self._toc_patterns:
                identifier = re.sub(pattern, replace, identifier)
            
            if identifier in self._toc_ids:
                self._toc_ids[identifier] += 1
                identifier = '{0}-{1}'.format(identifier, self._toc_ids[identifier])
            else:
                self._toc_ids[identifier] = 1
            
            new_leaf = _TOCLeaf(hlevel, identifier, text)
            
            if hlevel > self._toc_leaf.hlevel:
                new_leaf.parent = self._toc_leaf
                new_leaf.level = (self._toc_leaf.level + 1)
            elif hlevel < self._toc_leaf.hlevel:
                new_leaf.parent = self._toc_leaf.parent.parent
                new_leaf.level = (self._toc_leaf.level - 1)
            elif hlevel == self._toc_leaf.hlevel:
                new_leaf.parent = self._toc_leaf.parent
                new_leaf.level = self._toc_leaf.level
            
            if new_leaf.parent:
                new_leaf.parent.children.append(new_leaf)
            
            self._toc_leaf = new_leaf
            
            return '<h{0} id="{1}">{2}</h{0}>'.format(hlevel, identifier, text)
        else:
            return '<h{0}>{1}</h{0}>'.format(hlevel, text)
    
    
    def preprocess(self, markdown):
        
        if self.render_flags & h.HTML_TOC:
            self._toc_ids.clear()
            
            self.toc_tree = _TOCLeaf()
            self._toc_leaf = self.toc_tree
        
        return markdown
    
    def render(self, markdown):
        html = super(_Renderer, self).render(markdown)
        return html if (not self.render_flags & h.HTML_TOC) else (html, self.toc_tree)


class Parser(_Parser):
    accepts = ('.md', '.markdown')
    
    
    lookup = {
        'extensions': {
            'autolink': h.EXT_AUTOLINK,
            'disable_indented_code': h.EXT_DISABLE_INDENTED_CODE,
            'fenced_code': h.EXT_FENCED_CODE,
            'footnotes': h.EXT_FOOTNOTES,
            'highlight': h.EXT_HIGHLIGHT,
            'lax_spacing': h.EXT_LAX_SPACING,
            'no_intra_emphasis': h.EXT_NO_INTRA_EMPHASIS,
            'quote': h.EXT_QUOTE,
            'space_headers': h.EXT_SPACE_HEADERS,
            'strikethrough': h.EXT_STRIKETHROUGH,
            'superscript': h.EXT_SUPERSCRIPT,
            'tables': h.EXT_TABLES,
            'underline': h.EXT_UNDERLINE
        },
        'render_flags': {
            'escape': h.HTML_ESCAPE,
            'expand_tabs': h.HTML_EXPAND_TABS,
            'hard_wrap': h.HTML_HARD_WRAP,
            'safelink': h.HTML_SAFELINK,
            'skip_html': h.HTML_SKIP_HTML,
            'skip_images': h.HTML_SKIP_IMAGES,
            'skip_links': h.HTML_SKIP_LINKS,
            'skip_style': h.HTML_SKIP_STYLE,
            'smartypants': h.HTML_SMARTYPANTS,
            'toc': h.HTML_TOC,
            'use_xhtml': h.HTML_USE_XHTML
        }
    }
    
    defaults = {
        'extensions': {
            'autolink': True,
            'fenced_code': True,
            'footnotes': True,
            'no_intra_emphasis': True,
            'strikethrough': True,
            'tables': True
        },
        'render_flags': {
            'smartypants': True
        }
    }
    
    
    def parse(self, markdown):
        return self._md.render(markdown)
    
    def setup(self):
        self.flags = {}
        self.config = deepcopy(self.defaults)
        
        for k, v in self.options.iteritems():
            self.config[k].update(v)
        
        for group, options in self.config.iteritems():
            flags = [self.lookup[group][k] for k, v in options.iteritems() if v]
            
            self.flags[group] = reduce(or_, flags, 0)
        
        self._md = _Renderer(**self.flags)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import misaka as m

from mynt.base import Parser as _Parser


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
            'github_blockcode': m.HTML_GITHUB_BLOCKCODE,
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
            'github_blockcode': True,
            'hard_wrap': True,
            'smartypants': True
        }
    }
    
    flags = {
        'extensions': 0,
        'render_flags': 0
    }
    
    
    def parse(self, markdown):
        return m.html(markdown.encode('utf-8'), **self.flags).decode('utf-8')
    
    def setup(self):
        for k, v in self.options.iteritems():
            self.config[k].update(v)
        
        for group, options in self.config.iteritems():
            for option, value in options.iteritems():
                if value:
                    self.flags[group] |= self.lookup[group][option]

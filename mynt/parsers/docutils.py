# -*- coding: utf-8 -*-

from copy import deepcopy

from docutils import nodes, utils
from docutils.core import publish_parts
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.body import CodeBlock
from docutils.parsers.rst.roles import register_canonical_role, set_classes
from docutils.utils.code_analyzer import Lexer, LexerError
from docutils.writers.html4css1 import HTMLTranslator, Writer

from mynt.base import Parser as _Parser


def code_role(role, raw, string, lineno, inliner, options={}, content=[]):
    set_classes(options)
    language = options.get('language', '')
    classes = []

    if 'classes' in options:
        classes.extend(options['classes'])

    if language and language not in classes:
        classes.append(language)

    try:
        highlight = inliner.document.settings.syntax_highlight
        tokens = Lexer(utils.unescape(string, 1), language, highlight)
    except LexerError as error:
        message = inliner.reporter.warning(error)
        problem = inliner.problematic(raw, raw, message)

        return [problem], [message]

    node = nodes.literal(raw, '', classes=classes)

    for classes, value in tokens:
        if classes:
            node += nodes.inline(value, value, classes=classes)
        else:
            node += nodes.Text(value, value)

    return ([node], [])

code_role.options = {
    'class': directives.class_option,
    'language': directives.unchanged
}

register_canonical_role('code', code_role)


class _CodeBlock(CodeBlock):
    optional_arguments = 1
    option_spec = {
        'class': directives.class_option,
        'name': directives.unchanged,
        'number-lines': directives.unchanged}
    has_content = True

    def run(self):
        self.assert_has_content()

        if self.arguments:
            language = self.arguments[0]
        else:
            language = 'text'

        set_classes(self.options)
        classes = []

        if 'classes' in self.options:
            classes.extend(self.options['classes'])

        try:
            highlight = self.state.document.settings.syntax_highlight
            tokens = Lexer('\n'.join(self.content), language, highlight)
        except LexerError as error:
            raise self.warning(error)

        pre = nodes.literal_block(classes=classes)
        code = nodes.literal(classes=classes)
        code.attributes['data-lang'] = language
        self.add_name(pre)
        self.add_name(code)

        for classes, value in tokens:
            if classes:
                code += nodes.inline(value, value, classes=classes)
            else:
                code += nodes.Text(value, value)

        pre += code

        return [pre]

directives.register_directive('code', _CodeBlock)


class _Translator(HTMLTranslator):
    def set_first_last(self, node):
        pass

    def visit_bullet_list(self, node):
        attributes = {}
        self.context.append((self.compact_simple, self.compact_p))
        self.compact_p = None
        self.compact_simple = self.is_compactable(node)
        self.body.append(self.starttag(node, 'ul', '', **attributes))

    def visit_definition(self, node):
        self.body.append('</dt>')
        self.body.append(self.starttag(node, 'dd', ''))
        self.set_first_last(node)

    def depart_definition(self, node):
        self.body.append('</dd>')

    def visit_definition_list(self, node):
        self.body.append(self.starttag(node, 'dl', ''))

    def depart_definition_list(self, node):
        self.body.append('</dl>')

    def visit_entry(self, node):
        attributes = {}

        if isinstance(node.parent.parent, nodes.thead):
            tag = 'th'
        else:
            tag = 'td'

        node.parent.column += 1

        if 'morerows' in node:
            attributes['rowspan'] = node['morerows'] + 1

        if 'morecols' in node:
            attributes['colspan'] = node['morecols'] + 1
            node.parent.column += node['morecols']

        self.body.append(self.starttag(node, tag, '', **attributes))
        self.context.append('</{0}>'.format(tag.lower()))

        if len(node) == 0:
            self.body.append('&nbsp;')

        self.set_first_last(node)

    def visit_enumerated_list(self, node):
        attributes = {}

        if 'start' in node:
            attributes['start'] = node['start']

        self.context.append((self.compact_simple, self.compact_p))
        self.compact_p = None
        self.compact_simple = self.is_compactable(node)
        self.body.append(self.starttag(node, 'ol', '', **attributes))

    def visit_list_item(self, node):
        self.body.append(self.starttag(node, 'li', ''))

    def depart_list_item(self, node):
        self.body.append('</li>')

    def visit_literal(self, node):
        attributes = {}

        if 'data-lang' in node.attributes:
            attributes['data-lang'] = node.attributes['data-lang']

        self.body.append(self.starttag(node, 'code', '', **attributes))

    def visit_literal_block(self, node):
        self.body.append(self.starttag(node, 'pre', ''))

    def depart_literal_block(self, node):
        self.body.append('</pre>')

    def visit_paragraph(self, node):
        if self.should_be_compact_paragraph(node):
            self.context.append('')
        else:
            self.body.append(self.starttag(node, 'p', ''))
            self.context.append('</p>')

    def visit_reference(self, node):
        attributes = {}

        if 'refuri' in node:
            attributes['href'] = node['refuri']

            mailto = attributes['href'].startswith('mailto:')
            if self.settings.cloak_email_addresses and mailto:
                attributes['href'] = self.cloak_mailto(attributes['href'])
                self.in_mailto = True
        else:
            if 'refid' not in node:
                raise AttributeError(
                    'References must have `refuri` or `refid` attribute')

            attributes['href'] = '#' + node['refid']

        if not isinstance(node.parent, nodes.TextElement):
            if not (len(node) == 1 and isinstance(node[0], nodes.image)):
                raise Exception

        self.body.append(self.starttag(node, 'a', '', **attributes))

    def depart_row(self, node):
        self.body.append('</tr>')

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_table(self, node):
        self.body.append(self.starttag(node, 'table', ''))

    def depart_table(self, node):
        self.body.append('</table>')

    def visit_tbody(self, node):
        self.body.append(self.starttag(node, 'tbody', ''))

    def depart_tbody(self, node):
        self.body.append('</tbody>')

    def visit_tgroup(self, node):
        node.stubs = []

    def visit_thead(self, node):
        self.body.append(self.starttag(node, 'thead', ''))

    def depart_thead(self, node):
        self.body.append('</thead>')

    def visit_title(self, node):
        tag = '</p>'

        if isinstance(node.parent, nodes.topic):
            self.body.append(self.starttag(node, 'p', ''))
        elif isinstance(node.parent, nodes.sidebar):
            self.body.append(self.starttag(node, 'p', ''))
        elif isinstance(node.parent, nodes.Admonition):
            self.body.append(self.starttag(node, 'p', ''))
        elif isinstance(node.parent, nodes.table):
            self.body.append(self.starttag(node, 'caption', ''))
            tag = '</caption>'
        elif isinstance(node.parent, nodes.document):
            self.body.append(self.starttag(node, 'h1', ''))
            tag = '</h1>'
            self.in_document_title = len(self.body)
        else:
            if not isinstance(node.parent, nodes.section):
                raise Exception

            attributes = {}
            header_level = self.section_level + self.initial_header_level - 1

            self.body.append(self.starttag(
                node, 'h{0}'.format(header_level), ''))

            if node.hasattr('refid'):
                attributes['href'] = '#' + node['refid']

            if attributes:
                self.body.append(self.starttag({}, 'a', '', **attributes))

                tag = '</a></h{0}>'.format(header_level)
            else:
                tag = '</h{0}>'.format(header_level)

        self.context.append(tag)

class _Writer(Writer):
    def __init__(self):
        Writer.__init__(self)

        self.translator_class = _Translator


class Parser(_Parser):
    accepts = ('.rst',)
    defaults = {
        'doctitle_xform': 0,
        'input_encoding': 'utf-8',
        'output_encoding': 'utf-8',
        'report_level': 4,
        'smart_quotes': 1,
        'syntax_highlight': 'none'}


    def parse(self, restructuredtext):
        return publish_parts(
            restructuredtext,
            settings_overrides=self.configuration,
            writer=self._writer
        )['fragment']

    def setup(self):
        self.configuration = deepcopy(self.defaults)
        self.configuration.update(self.options)
        self.configuration['file_insertion_enabled'] = 0

        self._writer = _Writer()


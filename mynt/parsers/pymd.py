from mynt.base import Parser as _Parser
from markdown import Markdown


class Parser(_Parser):
    """Python-Markdown parser"""
    accepts = ('.md', '.markdown', '.text')

    defaults = {
        'extensions': (
            'extra',
            'codehilite',
        )
    }

    def parse(self, content):
        return self._md.convert(content)

    def setup(self):
        config = self.options or self.defaults
        self._md = Markdown(**config)

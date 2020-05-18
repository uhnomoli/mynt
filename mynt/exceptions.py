# -*- coding: utf-8 -*-


class MyntException(Exception):
    code = 1


    def __init__(self, message, *args):
        self.message = message
        self.debug = args


    def __str__(self):
        message = '!! {0}'.format(self.message)

        for line in self.debug:
            message += '\n..  {0}'.format(line.strip())

        return message


class ConfigurationException(MyntException):
    pass

class ContentException(MyntException):
    pass

class FileSystemException(MyntException):
    pass

class OptionException(MyntException):
    code = 2

class ParserException(MyntException):
    pass

class RendererException(MyntException):
    pass


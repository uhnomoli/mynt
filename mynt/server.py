# -*- coding: utf-8 -*-

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from mynt.utils import get_logger


logger = get_logger('mynt')


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client, base_url, server):
        self.base_url = base_url

        super().__init__(request, client, server)

    def do_GET(self):
        self.path = self.path.replace(self.base_url, '/')

        super().do_GET()

    def log_message(self, message, *args):
        logger.debug('>> [%s] %s: %s',
            self.log_date_time_string(), self.address_string(), message % args)

class Server(TCPServer):
    allow_reuse_address = True

    def __init__(self, server, base_url, handler, bind_and_activate=True):
        super().__init__(server, handler, bind_and_activate)

        self.base_url = base_url

    def finish_request(self, request, client):
        self.RequestHandlerClass(request, client, self.base_url, self)


#!/usr/bin/python
#coding:utf-8
from __future__ import division, print_function, absolute_import
import argparse
import socket
import webbrowser

from tornado import ioloop
from tornado.httpserver import HTTPServer

from pyf5.config import config
from pyf5.server import application
from pyf5.logger import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', dest='port', type=int, default=80)
    parser.add_argument('--debug', dest='debug', type=int, default=0 )
    args = parser.parse_args()

    server = HTTPServer(application)
    port = args.port
    for port in range(port, 90) + range(8000, 8100):
        try:
            server.listen(port)
            break
        except socket.error:
            warn('port {} is taken, trying next port...'.format(port))
            continue

    f5_url = 'http://127.0.0.1/_'
    if port != 80:
        f5_url = 'http://127.0.0.1:%s/_' % port
    info('F5 server started, please visit: {}'.format(f5_url))

    if not args.debug:
        webbrowser.open_new_tab('http://127.0.0.1:%s/_' % port)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        config.flush()
        info('Exiting...')
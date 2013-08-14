#!/usr/bin/python
#coding:utf-8
import socket
import webbrowser
from tornado import ioloop

from pyf5.server import F5Server
from pyf5.settings import CURRENT_MODE, PRODUCTION_MODE

if __name__ == '__main__':
    server = F5Server()
    port = 0
    for port in range(80, 90) + range(8000, 8100):
        try:
            server.listen(port)
            break
        except socket.error:
            continue

    print 'F5 server started, please visit:'
    print 'http://127.0.0.1/_' if port == 80 else 'http://127.0.0.1:%s/_' % port

    if CURRENT_MODE == PRODUCTION_MODE:
        webbrowser.open_new_tab('http://127.0.0.1:%s/_' % port)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'exit'
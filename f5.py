#!/usr/bin/python
#coding:utf-8
import socket
import webbrowser
from tornado import ioloop
from pyf5.server import F5Server, MODE, DEVELOP_MODE
from pyf5.utils import module_path

if __name__ == '__main__':
    path = module_path()
    server = F5Server()
    port = 0
    for port in range(80, 90) + range(8000, 8100):
        try:
            server.listen(port)
            break
        except socket.error:
            continue

    print 'F5 server started, please visit:'
    print '127.0.0.1' if port == 80 else '127.0.0.1:%s' % port

    if MODE != DEVELOP_MODE:
        webbrowser.open_new_tab('http://127.0.0.1:%s' % port)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'exit'
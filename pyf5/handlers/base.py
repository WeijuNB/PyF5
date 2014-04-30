#coding:utf-8
from datetime import datetime
import json

from tornado.web import RequestHandler, HTTPError

from ..utils import jsonable
from ..logger import *


class BaseRequestHandler(RequestHandler):
    def __repr__(self):
        return '[' + self.__class__.__name__ + ']'

    def post(self, path=None):
        self.handle(path)

    def get(self, path=None):
        self.handle(path)

    def handle(self, path):
        if not path:
            self.default()
        else:
            path = path.replace('.', '_').replace('/', '_')
            if path.startswith('_') or path in dir(BaseRequestHandler):
                raise HTTPError(500, 'ILLEGAL_PATH')
            elif hasattr(self, path):
                self.__getattribute__(path)()
            else:
                raise HTTPError(404)

    def default(self):
        raise HTTPError(404)

    def finish(self, chunk=None):
        """ 兼容 JSONP（需要有参数callback）
        """
        if chunk:
            callback = self.get_argument('callback', None)
            json_str = json.dumps(jsonable(chunk))
            debug(self, '->', json_str)
            if callback:
                self.write('%s(%s);' % (callback, json_str))
                self.set_header('Content-Type', 'application/x-javascript;charset=UTF-8')
            else:
                self.write(json_str)
                self.set_header('Content-Type', 'application/json;charset=UTF-8')
        RequestHandler.finish(self)
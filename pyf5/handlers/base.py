#coding:utf-8
from datetime import datetime
import json

from tornado.web import RequestHandler, HTTPError

from ..utils import jsonable
from ..logger import *


class BaseRequestHandler(RequestHandler):
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
        # override me
        raise HTTPError(404)

    def finish_json(self, data):
        """ 返回json/jsonp的数据
         如果argument中带有callback参数，则返回jsonp的script，否则返回json数据
        """
        callback = self.get_argument('callback', None)
        json_str = json.dumps(jsonable(data))
        debug('[' + self.__class__.__name__ + ']', '->', json_str)
        if callback:
            self.set_header('Content-Type', 'application/x-javascript;charset=UTF-8')
            self.write('%s(%s);' % (callback, json_str))
        else:
            self.set_header('Content-Type', 'application/json;charset=UTF-8')
            self.write(json_str)
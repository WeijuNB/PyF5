#coding:utf-8
from __future__ import absolute_import, division, print_function
from functools import partial
import json
import socket
import time

from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.web import RequestHandler, asynchronous, os, HTTPError


from ..config import config
from ..settings import CONFIG_PATH
from ..utils import jsonable, normalize_path
from ..logger import *
from .base import BaseRequestHandler


class BaseAPIHandler(BaseRequestHandler):
    def handle(self, path):
        if not path:
            self.default()
        else:
            path = path.replace('.', '_').replace('/', '_')
            if path.startswith('_') or path in dir(BaseRequestHandler):
                raise HTTPError(500, 'ILLEGAL_PATH')
            elif hasattr(self, path):
                data = self.request.arguments
                for key in data:
                    if type(data[key]) == list and len(data[key]) == 1:
                        data[key] = data[key][0]
                if self.request.method == 'POST':
                    try:
                        json_data = json.loads(self.request.body)
                        data.update(json_data)
                    except:
                        pass
                debug('[' + self.__class__.__name__ + ']', '<-', path, data)
                self.__getattribute__(path)(**data)
            else:
                raise HTTPError(404)

    def echo(self, **kwargs):
        self.finish_json(kwargs)


class ProjectAPIHandler(BaseAPIHandler):
    def list(self):
        return self.finish_json(
            config.get('projects', [])
        )

    def add(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if not project:
            config['projects'].append({
                'path': path
            })
            config.flush()
            return self.finish_json({'success': True})
        else:
            return self.finish_json({'error': 'Project Already Existed'})

    def select(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if project:
            for p in config['projects']:
                p['active'] = False
            project['active'] = True
            config.flush()
            self.finish_json({'success': True})
        else:
            self.finish_json({'error': 'Project Not Found'})

    def update(self, path, options):
        path = normalize_path(path)
        project = config.find_project(path)
        if not project:
            return self.finish_json({'error': 'Project Not Found'})

        project.update(options)
        config.flush()
        return self.finish_json({'success': True})

    def remove(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if project:
            config['projects'].remove(project)
            config.flush()
            return self.finish_json({'success': True})
        else:
            return self.finish_json({'error': 'Project Not Found'})


class FileSystemAPIHandler(BaseAPIHandler):
    def dir_list(self, path):
        pass

    def file_write(self, path, content):
        pass


class AppAPIHandler(BaseAPIHandler):
    def ver(self):
        pass


class APIRequestHandler(RequestHandler):
    def initialize(self):
        self.API_MAPPING = {
            'os': OSAPI,
            'project': ProjectAPI,
            'url': UrlAPI,
        }

    def setup(self):
        pass

    def handle_request(self):
        if self.request.headers.get('Origin'):
            self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
            self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        cmd_parts = self.path_args[0].split('/')
        if len(cmd_parts) > 2:
            return self.respond_error(INVALID_CMD, u'API路径不正确')
        method = cmd_parts[-1]
        category = cmd_parts[0] if len(cmd_parts) == 2 else None

        APIClass = self.API_MAPPING.get(category)
        if APIClass:
            self.__class__ = APIClass
            self.setup()

        apply(self.__getattribute__(method))

    @asynchronous
    def get(self, *args, **kwargs):
        self.handle_request()

    @asynchronous
    def post(self, *args, **kwargs):
        self.handle_request()

    @asynchronous
    def options(self, *args, **kwargs):
        if self.request.headers.get('Origin'):
            self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
            self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.finish()

    def respond_success(self, data=None):
        if not data:
            data = {}
        data['status'] = 'ok'
        self.respond_JSONP(data)

    def respond_error(self, error_name, error_message):
        data = {
            'status': 'error',
            'type': error_name,
            'message': error_message
        }
        self.respond_JSONP(data)

    def respond_JSONP(self, data):
        self.application.log_request(self)
        callback_name = self.get_argument('callback', None)
        json_data = json.dumps(jsonable(data))
        if callback_name:
            ret = '%s(%s);' % (callback_name, json_data)
        else:
            ret = json_data
        self.write(ret)
        self.finish()


class OSAPI(APIRequestHandler):
    def f5Version(self):
        return self.respond_success({'version': self.application.settings['version']})

    def listDir(self):
        path = self.get_argument('path', '')
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error(PATH_NOT_EXISTS, u'目录不存在:' + path)
        if not os.path.isdir(path):
            return self.respond_error(PATH_IS_NOT_DIR, u'路径不是目录')
        path = normalize_path(path)

        ret = []
        for name in os.listdir(path):
            abs_path = normalize_path(os.path.join(path, name))
            _, ext = os.path.splitext(name)
            is_dir = os.path.isdir(abs_path)
            ret.append(dict(
                name=name,
                absolutePath=abs_path,
                type='DIR' if is_dir else ext.replace('.', '').lower(),
            ))
        ret.sort(key=lambda item: (item['type'] != 'DIR', name))
        return self.respond_success({'list': ret})

    def writeFile(self):
        path = self.get_argument('path', '')
        content = self.get_argument('content', '')
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error(PATH_NOT_EXISTS, u'路径不存在:' + path)

        path = normalize_path(path)
        open(path, 'w').write(content.encode('utf-8'))
        return self.respond_success()

    def localHosts(self):
        result = socket.gethostbyname_ex(socket.gethostname())
        result = result[-1]
        if '127.0.0.1' not in result:
            result.insert(0, '127.0.0.1')
        return self.respond_success({'hosts': result})


class UrlAPI(APIRequestHandler):
    def setup(self):
        pass

    def checkAlive(self):
        url = self.get_argument('url', None)
        if not url:
            return self.respond_error(INVALID_PARAMS, u'缺少url参数')
        self.tryCheckAlive(url)

    def tryCheckAlive(self, url, count=0):
        client = AsyncHTTPClient()
        client.fetch(url, partial(self.checkAliveRespond, url, count), connect_timeout=1, request_timeout=1)

    def checkAliveRespond(self, url, count, response):
        if response.code / 100 in [2, 3]:
            return self.respond_success({})
        elif count > 3:
            return self.respond_error('NOT_ALIVE', u'目标网址不可用')
        else:
            ioloop.IOLoop.instance().add_timeout(time.time() + 1, lambda: self.tryCheckAlive(url, count + 1))
#coding:utf-8
from functools import partial
import json
import socket
import time

from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.web import RequestHandler, asynchronous, os

from pyf5.settings import CONFIG_PATH
from pyf5.models import Project
from pyf5.utils import jsonable, normalize_path


PATH_NOT_EXISTS = 'PATH_NOT_EXISTS'
INVALID_PARAMS = 'INVALID_PARAMS'
INVALID_CMD = 'INVALID_CMD'
PATH_IS_NOT_DIR = 'PATH_IS_NOT_DIR'
PROJECT_NOT_EXISTS = 'PROJECT_NOT_EXISTS'
PROJECT_EXISTS = 'PROJECT_EXISTS'


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
        print 'API:', self.request.uri, self.request.arguments


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


class ProjectAPI(APIRequestHandler):
    def setup(self):
        self.config = self.application.config
        self.projects = self.config.projects

    def _save_config(self):
        self.application.config.save(CONFIG_PATH)

    def _get_path_argument(self, argument_name, ensure_exists=False):
        path = self.get_argument(argument_name, '')
        if not path:
            self.respond_error(INVALID_PARAMS, u'缺少%s参数' % argument_name)
            return

        if ensure_exists and not os.path.exists(path):
            self.respond_error(INVALID_PARAMS, u'路径不存在：%s' % path)
            return

        return normalize_path(path)

    def _find(self, path):
        for project in self.projects:
            if project.path == path:
                return project

    def list(self):
        for project in self.projects:
            project.active = project == self.application.active_project
        self.respond_success({'projects': self.projects})

    def add(self):
        path = self._get_path_argument('path', True)
        if not path:
            return

        if path[-1] == '/':
            path = path[:-1]

        if self._find(path):
            return self.respond_error(PROJECT_EXISTS, u'项目已存在')

        project = Project(path=path)
        self.projects.append(project)

        self._save_config()
        self.respond_success({'project': project})

    def update(self):
        project = self.get_argument('project', None)
        try:
            data = json.loads(project)
            project = Project(**data)
        except Exception:
            return self.respond_error(INVALID_PARAMS, u'project参数不正确')

        found_index = -1
        for i, p in enumerate(self.projects):
            if p.path == project.path:
                found_index = i
        if found_index == -1:
            return self.respond_error(PROJECT_NOT_EXISTS, u'项目不存在')

        self.projects[found_index] = project
        if project.active:
            for p in self.projects:
                if p != project:
                    p.active = False
            self.application.load_project(project)

        self._save_config()
        return self.respond_success()

    def remove(self):
        path = self._get_path_argument('path')
        if not path:
            return

        project = self._find(path)
        if project:
            self.projects.remove(project)
        self._save_config()
        return self.list()


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
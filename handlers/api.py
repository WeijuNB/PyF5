#coding:utf-8
import json
from tornado.web import RequestHandler, asynchronous, os
from utils import get_rel_path


PATH_NOT_EXISTS = 'PATH_NOT_EXISTS'
INVALID_PARAMS = 'INVALID_PARAMS'
INVALID_CMD = 'INVALID_CMD'
PATH_IS_NOT_DIR = 'PATH_IS_NOT_DIR'
PROJECT_NOT_EXISTS = 'PROJECT_NOT_EXISTS'
PROJECT_EXISTS = 'PROJECT_EXISTS'


class APIRequestHandler(RequestHandler):
    def setup(self):
        pass

    @asynchronous
    def get(self, *args, **kwargs):
        cmd_parts = self.get_argument('cmd', None).split('.')
        if len(cmd_parts) > 2:
            return self.respond_error(INVALID_CMD, u'cmd格式不正确')
        method = cmd_parts[-1]
        category = cmd_parts[0] if len(cmd_parts) == 2 else None

        API_MAPPING = {
            'os': OSAPI,
            'project': ProjectAPI,
        }

        APIClass = API_MAPPING.get(category)
        if APIClass:
            self.__class__ = APIClass
            self.setup()

        apply(self.__getattribute__(method))

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
        callback_name = self.get_argument('callback', 'alert')
        json_data = json.dumps(data)
        ret = '%s(%s);' % (callback_name, json_data)
        self.write(ret)
        self.finish()
        print 'API:', '======================='
        print self.request.uri
        print json_data
        print '===================='


class OSAPI(APIRequestHandler):
    def listDir(self):
        path = self.get_argument('path', '')
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error(PATH_NOT_EXISTS, u'目录不存在:' + path)
        if not os.path.isdir(path):
            return self.respond_error(PATH_IS_NOT_DIR, u'路径不是目录')
        ret = []
        for name in os.listdir(path):
            abs_path = os.path.join(path, name)
            _, ext = os.path.splitext(name)
            is_dir = os.path.isdir(abs_path)
            ret.append(dict(
                name=name,
                absolutePath=abs_path.replace('\\', '/'),
                type='DIR' if is_dir else ext.replace('.', '').lower(),
            ))
        ret.sort(key=lambda item: (item['type'] != 'DIR', name))
        return self.respond_success({'list': ret})


class ProjectAPI(APIRequestHandler):
    def setup(self):
        self.config = self.application.config
        self.config.setdefault('projects', [])
        self.projects = self.config['projects']

    def save_config(self):
        self.application.save_config()

    def find(self, path):
        for project in self.projects:
            if project['path'] == path:
                return project

    def get_path_argument(self, key='path'):
        path = self.get_argument(key, '')
        return path.replace('\\', '/')

    def getCurrent(self):
        for project in self.projects:
            if project == self.application.project:
                return self.respond_success({'project': project})
        return self.respond_success({'project': None})

    def setCurrent(self):
        path = self.get_path_argument()
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error(PATH_NOT_EXISTS, u'目录不存在:' + path)

        for project in self.projects:
            if project.get('path') == path:
                self.application.set_project(project)
        self.save_config()
        return self.respond_success()

    def list(self):
        for project in self.projects:
            project['isCurrent'] = project == self.application.project
        self.respond_success({'projects': self.projects})

    def add(self):
        path = self.get_path_argument()
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error(PATH_NOT_EXISTS, u'路径不存在')

        for project in self.config['projects']:
            if project.get('path') == path:
                return self.respond_error(PROJECT_EXISTS, u'项目已存在')

        project = {'path': path}
        self.projects.append(project)

        self.save_config()
        return self.list()

    def remove(self):
        path = self.get_path_argument('path')
        if not path:
            return self.respond_error(INVALID_PARAMS, u'缺少path参数')
        project = self.find(path)
        if project:
            self.projects.remove(project)
        self.save_config()
        return self.list()

    def blockPaths(self):
        project_path = self.get_path_argument('projectPath')
        if not project_path:
            return self.respond_error(INVALID_PARAMS, u'缺少projectPath参数')
        if not os.path.exists(project_path):
            return self.respond_error(PATH_NOT_EXISTS, u'项目目录不存在：' + project_path)

        project = self.find(project_path)
        if not project:
            return self.respond_error(PROJECT_NOT_EXISTS, u'找不到项目')
        project.setdefault('blockPaths', [])
        paths = [os.path.join(project_path, block_path).replace('\\', '/')
                 for block_path in project['blockPaths']]
        return self.respond_success({'blockPaths': paths})

    def toggleBlockPath(self):
        project_path = self.get_path_argument('projectPath')
        if not project_path:
            return self.respond_error(INVALID_PARAMS, u'缺少projectPath参数')
        if not os.path.exists(project_path):
            return self.respond_error(PATH_NOT_EXISTS, u'项目目录不存在：' + project_path)

        block_path = self.get_path_argument('blockPath')
        if not block_path:
            return self.respond_error(INVALID_PARAMS, u'缺少blockPath参数')
        if not os.path.exists(block_path):
            return self.respond_error(PATH_NOT_EXISTS, u'屏蔽的目录不存在：' + block_path)

        action = self.get_argument('action', '')
        if not action or action not in ['on', 'off']:
            return self.respond_error(INVALID_PARAMS, u'缺少action参数或参数值不正确')

        project = self.find(project_path)
        if not project:
            return self.respond_error(PROJECT_NOT_EXISTS, u'找不到项目')

        rel_path = get_rel_path(block_path, project_path)
        if '..' in rel_path:
            return self.respond_error(INVALID_PARAMS, u'blockPath不属于ProjectPath')

        project_path = self.get_path_argument('projectPath')
        block_path = self.get_path_argument('blockPath')
        project = self.find(project_path)
        rel_path = get_rel_path(block_path, project_path)

        project.setdefault('blockPaths', [])
        if action == 'on' and not rel_path in project['blockPaths']:
            project['blockPaths'].append(rel_path)
        if action == 'off' and rel_path in project['blockPaths']:
            project['blockPaths'].remove(rel_path)
        self.save_config()
        return self.respond_success({})

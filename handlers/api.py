#coding:utf-8
import json
from tornado.web import RequestHandler, asynchronous, os


class APIRequestHandler(RequestHandler):
    def setup(self):
        pass

    @asynchronous
    def get(self, *args, **kwargs):
        cmd_parts = self.get_argument('cmd', None).split('.')
        if len(cmd_parts) > 2:
            return self.respond_error('INVALID_CMD', u'cmd格式不正确')
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
        self.write('%s(%s);' % (callback_name, json.dumps(data)))
        self.finish()


class OSAPI(APIRequestHandler):
    def listDir(self):
        path = self.get_argument('path', '')
        if not path:
            self.respond_error('INVALID_PARAMS', u'缺少path参数')
        if not os.path.exists(path):
            self.respond_error('PATH_NOT_EXISTS', u'目录不存在:' + path)
        if not os.path.isdir(path):
            self.respond_error('PATH_IS_NOT_DIR', u'路径不是目录')
        ret = []
        for name in os.listdir(path):
            abs_path = os.path.join(path, name)
            _, ext = os.path.splitext(name)
            is_dir = os.path.isdir(abs_path)
            ret.append(dict(
                name=name,
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

    def getCurrent(self):
        for project in self.projects:
            if project.get('isCurrent'):
                return self.respond_success({'project': project})

    def setCurrent(self):
        path = self.get_argument('path', '')
        if not path:
            return self.respond_error('INVALID_PARAMS', u'缺少path参数')
        if not os.path.exists(path):
            return self.respond_error('PATH_NOT_EXISTS', u'目录不存在:' + path)

        for project in self.projects:
            if project.get('path') == path:
                project['isCurrent'] = True
                self.application.set_site_path(path)
            else:
                project['isCurrent'] = False
        self.save_config()
        return self.respond_success()

    def all(self):
        self.respond_success({'projects': self.projects})

    def add(self):
        path = self.get_argument('path', '')
        if not path:
            self.respond_error('INVALID_PARAMS', u'缺少path参数')

        existed_project = None
        for project in self.config['projects']:
            if project.get('path') == path:
                existed_project = project
                break

        if not existed_project:
            project = {'path': path}
            self.projects.append(project)
        else:
            for project in self.config['projects']:
                if project['path'] == existed_project['path']:
                    project['isCurrent'] = True
                else:
                    project['isCurrent'] = False
        self.save_config()
        return self.all()

    def remove(self):
        path = self.get_argument('path', '')
        if not path:
            self.respond_error('INVALID_PARAMS', u'缺少path参数')
        project = self.find(path)
        if project:
            self.projects.remove(project)
        self.save_config()
        return self.all()
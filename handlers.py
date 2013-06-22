#coding:utf-8
import base64
import os
import json
import time
import cPickle
from StringIO import StringIO

from tornado.web import StaticFileHandler, RequestHandler, asynchronous, HTTPError
from tornado import ioloop

from utils import app_path, get_rel_path, we_are_frozen
from zfs import ZipFileSystem
from assets import assets_zip64


assets_zip_file = StringIO(base64.decodestring(assets_zip64))
zfs = ZipFileSystem(assets_zip_file)


class AssetsHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        StaticFileHandler.initialize(self, path, default_filename)

    def prepare(self):
        self.asset_path = self.path_args[0][1:]  # eg: '/js/reloader.js'[1:]

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        rel_path = get_rel_path(abspath, 'assets://')
        content = zfs.read(rel_path)
        return content

    def get_content_size(self):
        return zfs.file_size(self.asset_path) or 0

    def get_modified_time(self):
        return int(zfs.modified_at(self.asset_path)) or 0

    @classmethod
    def get_absolute_path(cls, root, path):
        return os.path.join('assets://', path)

    def validate_absolute_path(self, root, absolute_path):
        if not zfs.file_size(self.asset_path):
            raise HTTPError(404)
        return absolute_path


class StaticSiteHandler(StaticFileHandler):
    SCRIPT_AND_END_OF_BODY = '<script id="_f5_script" src="/_/js/reloader.js"></script>\n</body>'

    def should_return_304(self):
        return False

    @classmethod
    def is_html_path(cls, path):
        _, ext = os.path.splitext(path)
        if ext.lower() in ['.html', '.htm', '.shtml']:
            return True
        return False

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        if cls.is_html_path(abspath):
            html = open(abspath, 'r').read()
            html = html.replace('</body>', cls.SCRIPT_AND_END_OF_BODY)
            return html
        else:
            return StaticFileHandler.get_content(abspath, start, end)

    def get_content_size(self):
        if self.__class__.is_html_path(self.absolute_path):
            content = self.__class__.get_content(self.absolute_path)
            return len(content)
        else:
            return StaticFileHandler.get_content_size(self)


class ChangeRequestHandler(RequestHandler):
    def initialize(self):
        self.application.change_request_handlers.add(self)

        self.callback = self.get_argument('callback', '_F5.handleChanges')
        self.max_pending_time = 20
        self.query_time = time.time()

        deadline = time.time() + self.max_pending_time
        self.timeout = ioloop.IOLoop.instance().add_timeout(deadline, lambda: self.return_changes([]))

    @asynchronous
    def get(self, *args, **kwargs):
        pass

    def change_happened(self, all_changes):
        changes = []
        for change in all_changes:
            if change.time > self.query_time:
                changes.append(change)
        if changes:
            self.return_changes(changes)

    def return_changes(self, changes):
        ret = {
            'status': 'ok',
            'changes': [change._asdict() for change in changes],
        }
        ret = '%s(%s);' % (self.callback, json.dumps(ret))
        print ret
        self.write(ret)
        self.finish()
        ioloop.IOLoop.instance().remove_timeout(self.timeout)
        self.application.change_request_handlers.remove(self)


class APIRequestHandler(RequestHandler):
    @asynchronous
    def get(self, *args, **kwargs):
        cmd = self.get_argument('cmd', None)
        apply(self.__getattribute__(cmd))

    def getPath(self):
        self.return_success({'path': self.application.config.get('path', '')})

    def setPath(self):
        path = self.get_argument('path', '')
        if not path:
            return self.return_error('INVALID_PARAMS', u'缺少path参数')
        config = self.application.config
        if not os.path.exists(path):
            return self.return_error('PATH_NOT_EXISTS', u'目录不存在:' + path)
        config['path'] = path.replace('\\', '/')
        self.application.save_config()
        self.application.set_site_path(path)
        return self.return_success()

    def getPaths(self):
        self.return_success({'paths': self.application.config.get('paths', [])})

    def addPath(self):
        path = self.get_argument('path', '')
        if not path:
            self.return_error('INVALID_PARAMS', u'缺少path参数')
        config = self.application.config
        config.setdefault('paths', [])
        if path not in config['paths']:
            config['paths'].append(path)
            self.application.save_config()
        return self.getPaths()

    def delPath(self):
        path = self.get_argument('path', '')
        if not path:
            self.return_error('INVALID_PARAMS', u'缺少path参数')
        config = self.application.config
        config.setdefault('paths', [])
        if path in config['paths']:
            config['paths'].remove(path)
        return self.getPaths()

    def listDir(self):
        path = self.get_argument('path', '')
        if not path:
            self.return_error('INVALID_PARAMS', u'缺少path参数')
        if not os.path.exists(path):
            self.return_error('PATH_NOT_EXISTS', u'目录不存在:' + path)
        if not os.path.isdir(path):
            self.return_error('PATH_IS_NOT_DIR', u'路径不是目录')
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
        return self.return_success({'list': ret})

    def return_success(self, data=None):
        if not data:
            data = {}
        data['status'] = 'ok'
        self.return_JSONP(data)

    def return_error(self, error_name, error_message):
        data = {
            'status': 'error',
            'type': error_name,
            'message': error_message
        }
        self.return_JSONP(data)

    def return_JSONP(self, data):
        self.application.log_request(self)
        callback_name = self.get_argument('callback', 'alert')
        self.write('%s(%s);' % (callback_name, json.dumps(data)))
        self.finish()


if __name__ == '__main__':
    pass
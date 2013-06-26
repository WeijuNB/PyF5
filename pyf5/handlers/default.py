#coding:utf-8
import base64
import os
import json
import time
from StringIO import StringIO
from urllib import unquote

from tornado.web import StaticFileHandler, RequestHandler, asynchronous, HTTPError
from tornado import ioloop

from pyf5.utils import get_rel_path, we_are_frozen

assets_zip_file = None
VFS = None
if we_are_frozen():
    from pyf5.zfs import ZipFileSystem
    from pyf5.assets import assets_zip64
    assets_zip_file = StringIO(base64.decodestring(assets_zip64))
    VFS = ZipFileSystem(assets_zip_file)


class MarkDownHandler(RequestHandler):
    def get(self, *args, **kwargs):
        root_path = self.application.current_project_path()
        code = ''
        if root_path:
            rel_path = self.request.path[1:]
            rel_path = unquote(rel_path).decode('utf-8')
            md_path = os.path.join(root_path, rel_path).replace('\\', '/')
            code = open(md_path).read()
        print md_path
        self.render('edit.html',
                    code=code,
                    file_path=rel_path,
                    abs_path=md_path,
        )



class AssetsHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        StaticFileHandler.initialize(self, path, default_filename)

    def prepare(self):
        self.asset_path = self.path_args[0]  # eg: '/js/reloader.js'[1:]

    def should_return_304(self):
        return False

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        rel_path = get_rel_path(abspath, 'assets://')
        content = VFS.read(rel_path)
        return content

    def get_content_size(self):
        return VFS.file_size(self.asset_path) or 0

    def get_modified_time(self):
        return int(VFS.modified_at(self.asset_path)) or 0

    @classmethod
    def get_absolute_path(cls, root, path):
        return os.path.join('assets://', path)

    def validate_absolute_path(self, root, absolute_path):
        if not VFS.file_size(self.asset_path):
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
        self.init = self.get_argument('init', False)
        self.query_time = time.time()

        if self.get_argument('init', False):
            # 初次载入changes的时候，有可能因为长连接而会留下一个旋转的菊花，所以在初次请求的时候，比较快地返回数据
            # 让他快速进入第二个链接，希望能不出现菊花
            deadline = time.time() + 3
        else:
            deadline = time.time() + 20
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
        self.write(ret)
        self.finish()
        ioloop.IOLoop.instance().remove_timeout(self.timeout)
        self.application.change_request_handlers.remove(self)



#coding:utf-8
import base64
import os
from StringIO import StringIO
from urllib import unquote
import gc

from tornado.web import StaticFileHandler, RequestHandler, HTTPError

from pyf5.utils import get_rel_path, we_are_frozen, normalize_path
from pyf5.settings import RELOADER_TAG

assets_zip_file = None
VFS = None
if we_are_frozen():
    from pyf5.zfs import ZipFileSystem
    from pyf5.assets import assets_zip64
    assets_zip_file = StringIO(base64.decodestring(assets_zip64))
    VFS = ZipFileSystem(assets_zip_file)


class MarkDownHandler(RequestHandler):
    def get(self, *args, **kwargs):
        root_path = self.application.project.path
        rel_path = self.request.path[1:]
        rel_path = unquote(rel_path).decode('utf-8')
        md_path = os.path.join(root_path, rel_path).replace('\\', '/')
        code = open(md_path).read()
        print md_path
        self.render('edit.html',
                    code=code,
                    file_path=rel_path,
                    abs_path=md_path
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
        rel_path = normalize_path(abspath.replace('assets://', ''))
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
        gc.collect()  # 在mp4内容的时候，如果刷新网页会导致10053错误，并且内存不能回收，这里粗暴处理一下
        if cls.is_html_path(abspath):
            html = open(abspath, 'r').read()
            html = html.replace('</body>', RELOADER_TAG + '\n</body>')
            return html
        else:
            return StaticFileHandler.get_content(abspath, start, end)

    def get_content_size(self):
        if self.__class__.is_html_path(self.absolute_path):
            content = self.__class__.get_content(self.absolute_path)
            return len(content)
        else:
            return StaticFileHandler.get_content_size(self)

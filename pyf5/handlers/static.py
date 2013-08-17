#coding:utf-8
import base64
import os
from StringIO import StringIO
from urllib import unquote
import gc

from tornado.web import StaticFileHandler, RequestHandler, HTTPError

from pyf5.settings import CURRENT_MODE, PRODUCTION_MODE
from pyf5.handlers.helpers import process_html, HTML_EXTENSIONS, SPECIAL_EXTENSIONS,  CSS_EXTENSIONS, process_css
from pyf5.utils import normalize_path


class MarkDownHandler(RequestHandler):
    def get(self, *args, **kwargs):
        root_path = self.application.active_project.path
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


class ManagedFileHandler(StaticFileHandler):
    def should_return_304(self):
        return False

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        gc.collect()  # 在mp4内容的时候，如果刷新网页会导致10053错误，并且内存不能回收，这里粗暴处理一下
        _, ext = os.path.splitext(abspath)
        if ext in SPECIAL_EXTENSIONS:
            content = open(abspath, 'r').read()
            if ext in HTML_EXTENSIONS:
                return process_html(content)
            elif ext in CSS_EXTENSIONS:
                return process_css(content)
        return StaticFileHandler.get_content(abspath, start, end)

    def get_content_size(self):
        _, ext = os.path.splitext(self.absolute_path)
        if ext in SPECIAL_EXTENSIONS:
            content = self.__class__.get_content(self.absolute_path)
            return len(content)
        else:
            return StaticFileHandler.get_content_size(self)

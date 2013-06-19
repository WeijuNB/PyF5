#coding:utf-8
import base64
import os
import json
import time
import cPickle

from tornado.web import StaticFileHandler, RequestHandler, asynchronous, HTTPError

from utils import app_path, get_rel_path, we_are_frozen


vfs_dict = {}
assets_vfs = None
if we_are_frozen():
    from assets import pickle_base64
    from simple_vfs import VirtualFile, VFS
    vfs_dict = cPickle.loads(base64.decodestring(pickle_base64))
    assets_vfs = VFS(vfs_dict)


class StaticFileHandlerWithoutCache(StaticFileHandler):
    def should_return_304(self):
        return False


class AssetsHandler(StaticFileHandlerWithoutCache):
    def initialize(self, path, default_name=None):
        StaticFileHandlerWithoutCache.initialize(self, path, default_name)
        rel_path = get_rel_path(self.request.path, '/_f5/')
        self.vf = assets_vfs.get_file(rel_path)

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        rel_path = get_rel_path(abspath, app_path())
        vf = assets_vfs.get_file(rel_path)
        return [vf.bytes]

    def get_content_size(self):
        return self.vf.size

    def get_modified_time(self):
        return self.vf.modified_at

    @classmethod
    def get_absolute_path(cls, root, path):
        return os.path.join(app_path(), path)

    def validate_absolute_path(self, root, absolute_path):
        if not self.vf:
            raise HTTPError(404)
        return absolute_path


class HtmlFileHandler(StaticFileHandlerWithoutCache):
    SCRIPT_AND_END_OF_BODY = '<script id="_f5_script" src="_f5/js/reloader.js"></script>\n</body>'
    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        html = open(abspath, 'r').read()
        html = html.replace('</body>', cls.SCRIPT_AND_END_OF_BODY)
        return html

    def get_content_size(self):
        size = StaticFileHandlerWithoutCache.get_content_size(self)
        size = size - len('</body>') + len(self.__class__.SCRIPT_AND_END_OF_BODY)
        return size


class ChangeRequestHandler(RequestHandler):
    def initialize(self, refresher):
        self.refresher = refresher
        self.refresher.change_request_handlers.add(self)

        self.callback = self.get_argument('callback', '_F5.handleChanges')
        self.max_pending_time = 20
        self.query_time = time.time()

        deadline = time.time() + self.max_pending_time
        self.timeout = self.refresher._loop.add_timeout(deadline, lambda: self.return_changes([]))

    @asynchronous
    def get(self):
        pass

    def return_changes(self, changes):
        ret = {
            'status': 'ok',
            'changes': [change._asdict() for change in changes],
        }
        ret = '%s(%s);' % (self.callback, json.dumps(ret))
        print ret
        self.write(ret)
        self.finish()
        self.refresher._loop.remove_timeout(self.timeout)
        self.refresher.change_request_handlers.remove(self)

    def post(self):
        pass


if __name__ == '__main__':
    import base64
    import cPickle
    from simple_vfs import VFS
    vfs_dict = VFS.make_VFS_dict('assets')
    raw_data = cPickle.dumps(vfs_dict)
    wf = open('assets.py', 'w+')
    wf.write('pickle_base64 = """%s"""' % base64.encodestring(raw_data))
    wf.close()

    from assets import pickle_base64
    data = cPickle.loads(base64.decodestring(pickle_base64))
    print data
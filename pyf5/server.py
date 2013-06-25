#coding:utf-8
import os
import socket
import time
from collections import namedtuple
import cPickle

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, \
    EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from tornado import ioloop
from tornado.web import Application, RedirectHandler, StaticFileHandler

from pyf5.utils import module_path, get_rel_path, we_are_frozen, config_path
from pyf5.handlers import ChangeRequestHandler, AssetsHandler, StaticSiteHandler, APIRequestHandler

if we_are_frozen():
    # freeze 模式下面，使用打包的Assets文件
    pass
elif 'site-package' in module_path():
    # 源代码发布出去以后，使用最普通的StaticFileHandler
    AssetsHandler = StaticFileHandler
else:
    # 开发中，使用会自动更新的StaticSiteHandler
    AssetsHandler = StaticSiteHandler

Change = namedtuple('Change', 'time, path, type')


class ChangesObserver(FileSystemEventHandler):
    def __init__(self, changes_handler=None):
        self.observer = Observer()
        self.changes = []
        self.black_list = []
        self.path = None
        self.changes_handler = changes_handler
        self.changes_timer = None
        self.observer.start()

    def observe(self, path, black_list=None):
        self.path = path
        self.black_list = black_list or []
        self.observer.unschedule_all()
        self.observer.schedule(self, self.path, recursive=True)

    def get_changes_since(self, ts):
        ret = []
        for change in self.changes:
            if change[0] >= ts:
                ret.append(change)
        return ret

    def on_any_event(self, event):
        if event.is_directory:
            return
        now = time.time()
        rel_src_path = get_rel_path(event.src_path, self.path)

        if event.event_type == EVENT_TYPE_MOVED:
            self.add_pure_change(Change(now, rel_src_path, EVENT_TYPE_DELETED))
            rel_dest_path = get_rel_path(event.dest_path, self.path)
            self.add_pure_change(Change(now, rel_dest_path, EVENT_TYPE_CREATED))
        else:
            self.add_pure_change(Change(time.time(), rel_src_path, event.event_type))
        try:
            ioloop.IOLoop.instance().add_callback(self.refresh_change_timer)
        except RuntimeError:
            print 'ioloop.add_callback failed'

    def refresh_change_timer(self):
        loop = ioloop.IOLoop.instance()
        if self.changes_timer:
            loop.remove_timeout(self.changes_timer)
        self.changes_timer = loop.add_timeout(time.time() + 0.1, self.change_happened)

    def change_happened(self):
        if self.changes_handler and callable(self.changes_handler):
            ioloop.IOLoop.instance().add_callback(self.changes_handler)

    def find_related_trash_changes(self, change):
        trash_changes = []
        for old_change in self.changes[::-1]:
            if old_change.path != change.path or change.time - old_change.time > 0.1:
                continue

            if change.type == EVENT_TYPE_DELETED:
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_CREATED:
                    return trash_changes
            elif change.type == EVENT_TYPE_CREATED:
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_DELETED:
                    return trash_changes
        return []

    def add_pure_change(self, change):
        for path_name in self.black_list:
            if '..' not in os.path.relpath(change.path, path_name):
                print '...', change
                return

        trash_changes = self.find_related_trash_changes(change)
        if trash_changes:
            for change in trash_changes:
                self.changes.remove(change)
                print '-  ', change
        else:
            self.changes.append(change)
            print '+  ', change
        self.remove_outdated_changes(30)

    def remove_outdated_changes(self, seconds):
        for change in self.changes[:]:
            if change.time - time.time() > seconds:
                try:
                    self.changes.remove(change)
                except ValueError:
                    pass


class F5Server(Application):
    def __init__(self, handlers=None, default_host="", transforms=None, wsgi=False, **settings):
        if not handlers:
            handlers = [
                (r"/_/api/changes", ChangeRequestHandler),
                (r"/_/api/?(.*)", APIRequestHandler),
                (r"/_/?(.*)", AssetsHandler, {"path": os.path.join(module_path(), '_')}),
                (r"/", RedirectHandler, {'url': '/_/index.html'}),
            ]
        if not settings:
            settings = {'debug': True}
        if not default_host:
            default_host = '.*$'

        Application.__init__(self, handlers, default_host, transforms, wsgi, **settings)
        self.internal_handler_count = len(handlers)

        self.config_path = config_path()
        self.config = self.load_config()

        self.change_request_handlers = set()
        self.observer = ChangesObserver(changes_handler=self.change_happened)
        self.project = None

    def load_config(self):
        return cPickle.load(open(self.config_path)) if os.path.exists(self.config_path) else {}

    def save_config(self):
        cPickle.dump(self.config, open(self.config_path, 'w+'))

    def set_project(self, project):
        self.project = project
        path = project['path']
        black_list = project.get('blockPaths', [])

        if len(self.handlers) > 1:
            self.handlers.pop(-1)

        self.add_handlers(".*$", [
            (r"/(.*)", StaticSiteHandler, {"path": path})
        ])
        handle = self.handlers.pop(0)
        self.handlers.insert(self.internal_handler_count, handle)
        self.observer.observe(path, black_list)

    def change_happened(self):
        for handler in list(self.change_request_handlers):
            handler.change_happened(self.observer.changes)

if __name__ == "__main__":
    pass

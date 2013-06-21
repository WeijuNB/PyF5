#coding:utf-8
import os
import socket
import sys
import time
from threading import Thread
from collections import namedtuple

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, \
    EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from tornado import ioloop
from tornado.web import Application, StaticFileHandler

from utils import module_path, get_rel_path, we_are_frozen
from handlers import ChangeRequestHandler, AssetsHandler, StaticSiteHandler, APIRequestHandler

debug = True
if debug and not we_are_frozen():
    # 开发模式下面AssetsHandler就直接从开发目录下面读取assets
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

    def observe(self, path):
        self.path = path
        self.observer.unschedule_all()
        self.observer.schedule(self, self.path, recursive=True)

    def add_black_list(self, path_name_list):
        self.black_list = path_name_list

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
            if path_name in change.path:
                return

        trash_changes = self.find_related_trash_changes(change)
        if trash_changes:
            for change in trash_changes:
                self.changes.remove(change)
                print '-', change
        else:
            self.changes.append(change)
            print '+', change
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
            ]
        if not settings:
            settings = {'debug': debug}
        if not default_host:
            default_host = '.*$'

        Application.__init__(self, handlers, default_host, transforms, wsgi, **settings)
        self.internal_handler_count = len(handlers)
        self.path = ""

        self.change_request_handlers = set()
        self.observer = ChangesObserver(changes_handler=self.change_happened)

    def set_site_path(self, path):
        self.path = path
        if len(self.handlers) > 1:
            self.handlers.pop(-1)
        self.add_handlers(".*$", [
            (r"/(.*)", StaticSiteHandler, {"path": path})
        ])
        handle = self.handlers.pop(0)
        self.handlers.insert(self.internal_handler_count, handle)
        self.observer.observe(path)

    def change_happened(self):
        for handler in list(self.change_request_handlers):
            handler.change_happened(self.observer.changes)

if __name__ == "__main__":
    path = module_path()
    server = F5Server()
    port = 0
    for port in range(80, 90):
        try:
            server.listen(port)
            break
        except socket.error:
            continue
    print 'start on port:', port
    server.set_site_path(path)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'exit'

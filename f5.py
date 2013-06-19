#coding:utf-8
import os
import sys
import time
from threading import Thread
from collections import namedtuple

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, \
    EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from tornado import ioloop
from tornado.web import Application

from utils import module_path, get_rel_path, we_are_frozen
from handlers import StaticFileHandlerWithoutCache, HtmlFileHandler, ChangeRequestHandler, AssetsHandler


Change = namedtuple('Change', 'time, path, type')


class ReloadServer(Thread, FileSystemEventHandler):
    def __init__(self, port, path=None):
        Thread.__init__(self)

        if not path:
            path = module_path()
        self.path = path
        handlers = [
            (r"/_f5/changes", ChangeRequestHandler, dict(refresher=self)),
            (r"/_f5/(.*)", AssetsHandler if we_are_frozen() else StaticFileHandlerWithoutCache, {"path": os.path.join(module_path(), 'assets')}),
            (r"/(.*\.(:?html|htm|shtml))", HtmlFileHandler, {"path": path}),
            (r"/(.*)", StaticFileHandlerWithoutCache, {"path": path}),
        ]
        settings = {"debug": True}
        self.port = port

        self.server = Application(handlers, **settings)
        self.server.listen(self.port)

        self.observer = Observer()
        self.observer.schedule(self, path, recursive=True)

        self.change_request_handlers = set()
        self.changes = []  # list of Change within a certain period
        self.changes_timer = None

        self._stop = False
        self.daemon = True

    def stop(self):
        print 'Stop.'
        self._stop = self.__stop()
        self._loop.stop()

    def run(self):
        print 'Start.'
        self._loop = ioloop.IOLoop.instance()
        self.observer.start()
        self._loop.start()

    def get_changes_since(self, ts):
        ret = []
        for change in self.changes:
            if '.idea' in change.path:
                continue
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

        self._loop.add_callback(self.handle_changes)

    def add_pure_change(self, change):
        trash_changes = []
        trash_changes_valid = False
        for old_change in self.changes[::-1]:
            if old_change.path != change.path or change.time - old_change.time > 0.1:
                continue

            if change.type == EVENT_TYPE_DELETED:
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_CREATED:
                    trash_changes_valid = True
                    break
            elif change.type == EVENT_TYPE_CREATED:
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_DELETED:
                    trash_changes_valid = True
                    break

        if not trash_changes_valid:
            trash_changes = []

        if trash_changes:
            for change in trash_changes:
                self.changes.remove(change)
                print '-', change
        else:
            self.changes.append(change)
            print '+', change
        self.remove_outdated_changes(30)

    def remove_outdated_changes(self, seconds):
        while 1:
            if len(self.changes) == 0:
                break
            change = self.changes[0]
            if change.time - time.time() > seconds:
                self.changes.pop(0)
            else:
                break

    def handle_changes(self):
        if self.changes_timer:
            self._loop.remove_timeout(self.changes_timer)
        self.changes_timer = self._loop.add_timeout(time.time() + 0.1, self.respond_change_requests)

    def respond_change_requests(self):
        if self.change_request_handlers:
            for handler in list(self.change_request_handlers):
                changes = self.get_changes_since(handler.query_time)
                if changes:
                    handler.return_changes(changes)


if __name__ == "__main__":
    try:
        server = ReloadServer(80)
        server.start()
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print 'Exit.'
        sys.exit(0)
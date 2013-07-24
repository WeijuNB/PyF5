#coding:utf-8
import json
import time
from tornado import ioloop
from tornado.web import RequestHandler, asynchronous


class ChangeRequestHandler(RequestHandler):
    handlers = set()

    @classmethod
    def broadcast_changes(cls):
        handlers = list(cls.handlers)
        for handler in handlers:
            changes = handler.application.watcher.get_changes_since(handler.query_time)
            if changes:
                handler.respond_changes(changes)

    def initialize(self):
        self.handlers.add(self)
        self.timeout = None

        self.callback_name = self.get_argument('callback', '_F5.handleChanges')
        self.delay = int(self.get_argument('delay', 20))
        self.query_time = float(self.get_argument('ts', time.time()))

    @asynchronous
    def get(self, *args, **kwargs):
        changes = self.application.watcher.get_changes_since(self.query_time)
        if changes:
            self.respond_changes(changes)
        else:
            deadline = time.time() + self.delay
            self.timeout = ioloop.IOLoop.instance().add_timeout(deadline, lambda: self.respond_changes([]))

    def respond_changes(self, changes):
        self.set_header('Content-Type', "text/javascript")
        ret = '%s(%s);' % (self.callback_name, json.dumps({
            'status': 'ok',
            'time': time.time(),
            'changes': [change.dict() for change in changes],
        }))
        self.write(ret)

        if self.timeout:
            ioloop.IOLoop.instance().remove_timeout(self.timeout)
            self.timeout = None

        self.finish()
        self.handlers.remove(self)

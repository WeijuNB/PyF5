#coding:utf-8
from datetime import timedelta
from functools import partial
import json
import time

from tornado import ioloop
from tornado.web import asynchronous

from ..settings import CHANGE_DEBOUNCE_TIME, CHANGE_INIT_PULL_TIME, CHANGE_MAX_PULL_TIME
from .base import BaseRequestHandler



class ChangeRequestHandler(BaseRequestHandler):
    handlers = set()
    changes = []
    debounce_timeout = None
    ioloop = ioloop.IOLoop.current()

    def __init__(self, *args, **kwargs):
        BaseRequestHandler.__init__(self, *args, **kwargs)
        self.handlers.add(self)

        self.callback_name = self.get_argument('callback', '_F5.handleChanges')
        self.delay = int(self.get_argument('delay', CHANGE_INIT_PULL_TIME))
        self.query_time = time.time()

        self.reply_timeout = None

    def on_finish(self):
        self.handlers.remove(self)
        if self.reply_timeout:
            self.ioloop.remove_timeout(self.reply_timeout)
            self.reply_timeout = None

    @classmethod
    def add_change(cls, change):
        # todo filter change
        cls.changes.append(change)

        if cls.debounce_timeout:
            cls.ioloop.remove_timeout(cls.debounce_timeout)
        cls.debounce_timeout = cls.ioloop.add_timeout(timedelta(seconds=CHANGE_DEBOUNCE_TIME), cls.push_changes)

    @classmethod
    def push_changes(cls):
        for handler in cls.handlers:
            handler.respond_changes([])

    def get_changes(self):
        return []

    @asynchronous
    def get(self, *args, **kwargs):
        changes = self.get_changes()
        if changes:
            self.respond_changes(changes)
        else:
            self.reply_timeout = self.ioloop.add_timeout(timedelta(seconds=self.delay), partial(self.respond_changes, []))

    def respond_changes(self, changes):
        data = {
            'changes': changes
        }
        self.finish(data)
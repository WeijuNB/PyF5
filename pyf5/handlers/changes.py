#coding:utf-8
from __future__ import print_function, division, absolute_import
from datetime import timedelta
from functools import partial
import time

from tornado import ioloop
from tornado.web import asynchronous
from watchdog.events import EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED

from ..settings import PUSH_CHANGES_DEBOUNCE_TIME
from ..utils import path_is_parent
from ..config import config
from ..logger import *
from .base import BaseRequestHandler


class ChangeRequestHandler(BaseRequestHandler):
    handlers = set()
    changes = []
    push_debounce_timer = None

    def __init__(self, *args, **kwargs):
        BaseRequestHandler.__init__(self, *args, **kwargs)
        self.handlers.add(self)

        self.callback_name = self.get_argument('callback', '_F5.handleChanges')
        self.delay = int(self.get_argument('delay', 20))
        self.query_time = int(self.get_argument('delay', 20))

        self.reply_timer = None

    @asynchronous
    def get(self, *args, **kwargs):
        self.reply_timer = ioloop.IOLoop.current().add_timeout(timedelta(seconds=self.delay), partial(self.respond_changes, []))

    def respond_changes(self, changes):
        ret = {'changes': {}}

        for change in changes:
            ret['changes'][change['path']] = {
                'time': change['time'],
                'type': change['type']
            }

        self.finish(ret)

    def on_finish(self):
        self.handlers.remove(self)
        if self.reply_timer:
            ioloop.IOLoop.current().remove_timeout(self.reply_timer)
            self.reply_timer = None

    @classmethod
    def add_change(cls, change):  # change: time, path, type
        project = config.current_project()
        if not project or not path_is_parent(project['path'], change['path']):
            return

        # todo: filter change

        trash_changes = cls.find_trash_changes(change)
        if trash_changes:
            debug('~', change)
            for change in trash_changes:
                debug('-', change)
                cls.changes.remove(change)
        else:
            debug('+', change)
            cls.changes.append(change)

        if cls.push_debounce_timer:
            ioloop.IOLoop.current().remove_timeout(cls.push_debounce_timer)

        cls.push_debounce_timer = ioloop.IOLoop.current().add_timeout(
            timedelta(seconds=PUSH_CHANGES_DEBOUNCE_TIME),
            cls.push_changes
        )

    @classmethod
    def find_trash_changes(cls, change):
        """ 寻找当前change之前短时间内的一些垃圾change
        有些编辑器喜欢用 改名->写入->改回名 的方式来保存文件，所以不能直接将change上报，需要进行一定的过滤
        """
        trash_changes = []
        for old_change in cls.changes[::-1]:
            if old_change['path'] != change['path']:
                continue
            if change['time'] > old_change['time'] + 1:
                break

            if change['type'] == EVENT_TYPE_DELETED:
                # 如果当前change类型是DELETED，那么返回所有该文件的事件，直到CREATED事件为止
                trash_changes.append(old_change)
                if old_change['type'] == EVENT_TYPE_CREATED:
                    return trash_changes
            elif change['type'] == EVENT_TYPE_CREATED:
                # 如果当前change类型是CREATED，那么返回所有该文件的事件，直到DELETED事件为止
                trash_changes.append(old_change)
                if old_change['type'] == EVENT_TYPE_DELETED:
                    return trash_changes
        return []

    @classmethod
    def push_changes(cls):
        debug('push changes', cls.changes)
        for handler in list(cls.handlers):
            handler.respond_changes(cls.changes)
        for change in cls.changes:
            mark = '?'
            if change['type'] == EVENT_TYPE_CREATED:
                mark = '+'
            elif change['type'] == EVENT_TYPE_DELETED:
                mark = '-'
            elif change['type'] == EVENT_TYPE_MODIFIED:
                mark = '*'
            info('->', mark, change['path'])
        cls.changes = []



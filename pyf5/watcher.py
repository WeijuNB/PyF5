#coding:utf-8
from __future__ import division, print_function, absolute_import
from datetime import timedelta
import os
import sys
import time

from tornado import ioloop
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, \
    EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, LoggingEventHandler
from watchdog.observers import Observer

from .logger import *
from .config import config
from .utils import normalize_path
from .handlers.changes import ChangeRequestHandler


class Watcher(FileSystemEventHandler):
    def __init__(self):
        self.ioloop = ioloop.IOLoop.current()

        self.observer = Observer()
        self.observer.start()
        self.path = None

    def __repr__(self):
        return '[{}]'.format(self.__class__.__name__)

    def watch(self, path):
        if path != self.path:
            info(self, 'watch', path)
            self.observer.unschedule_all()
            self.observer.schedule(self, path, True)
            self.path = path

    def stop(self):
        debug(self, 'stop watch all')
        self.observer.unschedule_all()

    def check_folder_change(self, folder_path):
        now = time.time() - 0.5  # 0.5秒内的都算修改
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if not os.path.isfile(file_path):
                continue

            modified_time = os.path.getmtime(file_path)
            if modified_time > now:
                self.on_any_event(FileModifiedEvent(file_path))

    def on_any_event(self, event):
        debug(self, '<-', 'D' if event.is_directory else 'F', event.event_type, event.src_path)

        if event.is_directory:
            if not sys.platform.startswith('win'):
                self.check_folder_change(event.src_path)
            return

        now = time.time()
        if event.event_type == EVENT_TYPE_MOVED:
            self.add_change(dict(
                time=now,
                path=normalize_path(event.src_path),
                type=EVENT_TYPE_DELETED
            ))
            self.add_change(dict(
                time=now,
                path=normalize_path(event.dest_path),
                type=EVENT_TYPE_CREATED
            ))
        else:
            self.add_change(dict(
                time=now,
                path=normalize_path(event.src_path),
                type=event.event_type
            ))

    def add_change(self, change):
        ioloop.IOLoop.current().add_callback(ChangeRequestHandler.add_change, change)


watcher = Watcher()
project = config.current_project()
if project:
    watcher.watch(project['path'])

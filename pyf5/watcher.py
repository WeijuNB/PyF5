#coding:utf-8
from collections import namedtuple
import os
import time
from tornado import ioloop
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED
from watchdog.observers import Observer
from models import Change
from utils import get_rel_path, path_is_parent


class ChangesWatcher(FileSystemEventHandler):
    def __init__(self, changes_handler=None):
        self.observer = Observer()
        self.changes = []
        self.mute_list = []
        self.path = None
        self.changes_handler = changes_handler
        self.changes_timer = None
        self.observer.start()

    def observe(self, path, mute_list=None):
        self.path = path
        self.mute_list = mute_list or []
        self.observer.unschedule_all()
        self.observer.schedule(self, self.path, recursive=True)

    def get_changes_since(self, timestamp):
        ret = []
        for change in self.changes:
            if change.timestamp > timestamp:
                ret.append(change)
        return ret

    def add_pure_change(self, change):
        """ 监测change的类型，并添加非垃圾change和不在黑名单中的change
        """

        # 如果是黑名单及黑名单子目录的change，则跳过
        for black_path in self.mute_list:
            if path_is_parent(black_path, change.path):
                print '...', change
                return

        # 寻找当前change对应的垃圾change，找到后删除；未找到则添加当前change
        trash_changes = self.find_related_trash_changes(change)
        if trash_changes:
            for change in trash_changes:
                self.changes.remove(change)
                print '-  ', change
        else:
            self.changes.append(change)
            print '+  ', change

        ioloop.IOLoop.instance().add_callback(lambda: self.remove_outdated_changes(30))

    def on_any_event(self, event):
        if event.is_directory:
            return

        now = time.time()
        src_relative_path = get_rel_path(event.src_path, self.path)

        if event.event_type == EVENT_TYPE_MOVED:
            self.add_pure_change(Change(timestamp=now, path=src_relative_path, type=EVENT_TYPE_DELETED))
            dest_relative_path = get_rel_path(event.dest_path, self.path)
            self.add_pure_change(Change(timestamp=now, path=dest_relative_path, type=EVENT_TYPE_CREATED))
        else:
            self.add_pure_change(Change(timestamp=now, path=src_relative_path, type=event.event_type))

        try:
            print '############# callback:notify_changes_with_delay ############'
            self.notify_changes_with_delay()
        except RuntimeError:
            print 'ioloop.add_callback failed'

    def notify_changes_with_delay(self):
        loop = ioloop.IOLoop.instance()
        if self.changes_timer:
            print '########## kill changes_handlers 0.1s later #############'
            loop.remove_timeout(self.changes_timer)

        if self.changes_handler and callable(self.changes_handler):
            print '########## call changes_handlers 0.1s later #############', time.time()
            self.changes_timer = loop.add_timeout(time.time() + 0.1, self.changes_handler)

    def find_related_trash_changes(self, change):
        """ 寻找当前change之前短时间内的一些垃圾change
        有些编辑器喜欢用 改名->写入->改回名 的方式来保存文件，所以不能直接将change上报，需要进行一定的过滤
        """
        trash_changes = []
        for old_change in self.changes[::-1]:
            if old_change.path != change.path:
                continue
            if change.timestamp - old_change.timestamp > 0.1:
                break

            if change.type == EVENT_TYPE_DELETED:
                # 如果当前change类型是DELETED，那么返回所有该文件的change事件，直到CREATED事件为止
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_CREATED:
                    return trash_changes
            elif change.type == EVENT_TYPE_CREATED:
                # 如果当前change类型是CREATED，那么返回所有该文件的change事件，直到DELETED事件为止
                trash_changes.append(old_change)
                if old_change.type == EVENT_TYPE_DELETED:
                    return trash_changes
        return []

    def remove_outdated_changes(self, seconds):
        for change in self.changes[:]:
            if change.timestamp - time.time() > seconds:
                self.changes.remove(change)

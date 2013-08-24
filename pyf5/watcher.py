#coding:utf-8
import os
import sys
import time

from tornado import ioloop
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, \
    EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED
from watchdog.observers import Observer

from pyf5.models import Change
from pyf5.settings import DEFAULT_MUTE_LIST, APP_FOLDER, NODE_BIN_PATH
from pyf5.utils import get_rel_path, path_is_parent, normalize_path, run_cmd


class ChangesWatcher(FileSystemEventHandler):
    def __init__(self, application):
        self.application = application
        self.observer = Observer()
        self.changes = []
        self.mute_list = []
        self.path = None
        self.changes_timer = None
        self.observer.start()

    def observe(self, path, mute_list=None):
        self.path = path
        self.mute_list = (mute_list or []) + DEFAULT_MUTE_LIST
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
                print '...', change.type, change.path
                return

        # 寻找当前change对应的垃圾change，找到后删除；未找到则添加当前change
        trash_changes = self.find_related_trash_changes(change)
        if trash_changes:
            for change in trash_changes:
                self.changes.remove(change)
                print '-  ', change.type, change.path
        else:
            self.changes.append(change)
            print '+  ', change.type, change.path
            self.compile_if_necessary(change)

        ioloop.IOLoop.instance().add_callback(lambda: self.remove_outdated_changes(30))

    def compile_if_necessary(self, change):
        if change.type == EVENT_TYPE_DELETED:
            return

        input_path = normalize_path(os.path.join(self.path, change.path))
        base_path, ext = os.path.splitext(input_path)
        ext = ext.lower()
        if ext not in['.less', '.coffee']:
            return

        active_project = self.application.active_project
        if not active_project:
            return

        os.chdir(APP_FOLDER)
        begin_time = time.time()
        if ext == '.less':
            if active_project.compileLess:
                output_path = base_path + '.css'
                run_cmd('%s bundled/less/bin/lessc %s %s' % (NODE_BIN_PATH, input_path, output_path))
                print 'compile:', change.path, time.time() - begin_time, 'seconds'
            else:
                print 'skip compile', change.path, '(OFF by settings)'

        elif ext == '.coffee':
            if active_project.compileCoffee:
                run_cmd('%s bundled/coffee/bin/coffee --compile %s' % (NODE_BIN_PATH, input_path))
                print 'compile:', change.path, time.time() - begin_time, 'seconds'
            else:
                print 'skip compile', change.path, '(OFF by settings)'

    def if_folder_changed(self, folder_path):
        if sys.platform.startswith('win'):
            return
        if not os.path.isdir(folder_path):
            return  # ignore

        now = time.time() - 2.5  # 2.5秒内的都算修改
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if not os.path.isfile(file_path):
                continue

            modified_time = os.path.getmtime(file_path)
            if modified_time > now:
                self.on_any_event(FileModifiedEvent(file_path))

    def on_any_event(self, event):
        if event.is_directory:
            self.if_folder_changed(event.src_path)
            return

        # 暂停文件变更的上报, 以免中途编译占用太长时间，而将事件提前返回
        loop = ioloop.IOLoop.instance()
        if self.changes_timer:
            ioloop.IOLoop.instance().remove_timeout(self.changes_timer)

        now = time.time()
        src_relative_path = get_rel_path(event.src_path, self.path)

        if event.event_type == EVENT_TYPE_MOVED:
            self.add_pure_change(Change(dict(timestamp=now, path=src_relative_path, type=EVENT_TYPE_DELETED)))
            dest_relative_path = get_rel_path(event.dest_path, self.path)
            self.add_pure_change(Change(dict(timestamp=now, path=dest_relative_path, type=EVENT_TYPE_CREATED)))
        else:
            self.add_pure_change(Change(dict(timestamp=now, path=src_relative_path, type=event.event_type)))

        # 延迟0.1秒上报变更，防止有些事件连续发生时错过
        self.changes_timer = loop.add_timeout(time.time() + 0.1, self.application.project_file_changed)

    def find_related_trash_changes(self, change):
        """ 寻找当前change之前短时间内的一些垃圾change
        有些编辑器喜欢用 改名->写入->改回名 的方式来保存文件，所以不能直接将change上报，需要进行一定的过滤
        """
        trash_changes = []
        for old_change in self.changes[::-1]:
            if old_change.path != change.path:
                continue
            if change.timestamp - old_change.timestamp > 1:
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
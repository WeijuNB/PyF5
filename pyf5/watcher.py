#coding:utf-8
import os
import time

from tornado import ioloop
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED
from watchdog.observers import Observer

from pyf5.models import Change
from pyf5.settings import DEFAULT_MUTE_LIST, APP_FOLDER
from pyf5.utils import get_rel_path, path_is_parent, normalize_path


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

        abs_path = normalize_path(os.path.join(self.path, change.path))
        base_path, ext = os.path.splitext(abs_path)
        ext = ext.lower()

        if ext not in['.less', '.coffee']:
            return

        if not self.application.active_project:
            return

        active_project = self.application.active_project
        begin_time = time.time()
        os.chdir(APP_FOLDER)
        if ext == '.less':
            if active_project.compileLess:
                output_path = base_path + '.css'
                cmd = 'bundled/node.exe bundled/less/bin/lessc %s %s' % (abs_path, output_path)
                os.system(cmd.replace('/', '\\'))
                print 'compile:', change.path, time.time() - begin_time, 'seconds'
            else:
                print 'skip compile', change.path, '(setting is off)'
        elif ext == '.coffee':
            if active_project.compileCoffee:
                output_path = base_path + '.js'
                cmd = 'bundled/node.exe bundled/coffee/bin/coffee --compile %s' % (abs_path, )
                os.system(cmd.replace('/', '\\'))
                print 'compile:', change.path, time.time() - begin_time, 'seconds'
            else:
                print 'skip compile', change.path, '(setting is off)'

    def on_any_event(self, event):
        if event.is_directory:
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

#coding:utf-8
import os
import cPickle

from tornado.web import Application, RedirectHandler, StaticFileHandler
from handlers.changes import ChangeRequestHandler
from handlers.proxy import ForwardRequestHandler
from watcher import ChangesWatcher
from models import Config

from pyf5.utils import module_path, config_path, get_current_mode, FREEZE_MODE, PACKAGE_MODE, DEVELOP_MODE
from pyf5.handlers import AssetsHandler, StaticSiteHandler, APIRequestHandler, MarkDownHandler

MODE = get_current_mode()
if MODE == FREEZE_MODE:
    # freeze 模式下面，使用打包的Assets文件（默认）
    pass
elif MODE == PACKAGE_MODE:
    # 源代码发布出去以后，使用最普通的StaticFileHandler
    AssetsHandler = StaticFileHandler
elif MODE == DEVELOP_MODE:
    # 开发中，使用会自动更新的StaticSiteHandler
    AssetsHandler = StaticSiteHandler


class F5Server(Application):
    def __init__(self):
        handlers = [
            (r"/_/api/changes", ChangeRequestHandler),
            (r"/_/api/(.*)", APIRequestHandler),
            (r"/_/(.+)", AssetsHandler, {"path": os.path.join(module_path(), '_')}),
            # (r"/", RedirectHandler, {'url': '/_/index.html'}),
        ]
        self._handlers_count = len(handlers)
        settings = {
            'debug': True,
            'template_path': os.path.join(module_path(), '_'),
        }

        Application.__init__(self, handlers, ".*$", None, False, **settings)

        if self.project:
            self.load_project(self.project)

    @property
    def watcher(self):
        if not hasattr(self, '_watcher'):
            self._watcher = ChangesWatcher(changes_handler=self.project_file_changed)
        return self._watcher

    @property
    def config(self):
        if not hasattr(self, '_config'):
            path = config_path()
            if os.path.exists(path):
                self._config = Config.load(path)
            else:
                self._config = Config()
                self._config.path = path
        return self._config

    @property
    def project(self):
        for project in self.config.projects:
            if project.active:
                return project
        return None

    def load_project(self, target_project):
        found = False
        for old_project in self.config.projects:
            old_project.active = False
            if old_project.path == target_project.path:
                old_project.active = True
                found = True

        if not found:
            self.config.projects.append(target_project)
            target_project.active = True

        if len(self.handlers) > 1:
            self.handlers.pop(-1)
        if target_project.targetHost:
            self.add_handlers(".*$", [
                (r"/_/?", RedirectHandler, {'url': '/_/index.html'}),
                (r"/(.*)", ForwardRequestHandler),
            ])
            ForwardRequestHandler.forward_host = target_project.targetHost
        else:
            self.add_handlers(".*$", [
                (r"/_?/?", RedirectHandler, {'url': '/_/index.html'}),
                (r"/(.*)\.md", MarkDownHandler),
                (r"/(.*)", StaticSiteHandler, {"path": target_project.path}),
            ])
        handle = self.handlers.pop(0)
        self.handlers.insert(self._handlers_count, handle)

        self.watcher.observe(target_project.path, target_project.muteList)
        if MODE == DEVELOP_MODE:
            self.watcher.observer.schedule(self.watcher, module_path(), recursive=True)

    def current_project_path(self):
        if not self.project:
            return None
        return self.project.path

    def project_file_changed(self):
        ChangeRequestHandler.broadcast_changes()


if __name__ == "__main__":
    pass

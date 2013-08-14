#coding:utf-8
import os

from tornado.web import Application, RedirectHandler, StaticFileHandler

from pyf5.settings import CURRENT_MODE, VERSION, PRODUCTION_MODE, DEVELOPMENT_MODE, RESOURCE_FOLDER, CONFIG_PATH, APP_FOLDER
from pyf5.models import Config
from pyf5.watcher import ChangesWatcher
from pyf5.handlers.api import APIRequestHandler
from pyf5.handlers.static import MarkDownHandler, ManagedFileHandler
from pyf5.handlers.proxy import ForwardRequestHandler
from pyf5.handlers.changes import ChangeRequestHandler


# will live reload F5 dashboard
if CURRENT_MODE == DEVELOPMENT_MODE:
    ResourceHandler = ManagedFileHandler
if CURRENT_MODE == PRODUCTION_MODE:
    ResourceHandler = StaticFileHandler


class F5Server(Application):
    def __init__(self):
        handlers = [
            (r"/_/api/changes", ChangeRequestHandler),
            (r"/_/api/(.*)", APIRequestHandler),
            (r"/_/(.+)", ResourceHandler, {"path": RESOURCE_FOLDER}),
            (r"/_/?", RedirectHandler, {'url': '/_/index.html?ver=' + VERSION}),
            # (r"/", RedirectHandler, {'url': '/_/index.html'}),
        ]
        self._handlers_count = len(handlers)
        settings = {
            'debug': True,
            'template_path': RESOURCE_FOLDER,
            'version': VERSION
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
            if os.path.exists(CONFIG_PATH):
                self._config = Config.load(CONFIG_PATH)
            else:
                self._config = Config()
                self._config.path = CONFIG_PATH
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
            self.add_handlers(".*$", [(r"/(.*)", ForwardRequestHandler)])
            ForwardRequestHandler.forward_host = target_project.targetHost
        else:
            self.add_handlers(".*$", [
                (r"/", RedirectHandler, {'url': '/_/index.html?ver=' + VERSION}),
                (r"/(.*)\.md", MarkDownHandler),
                (r"/(.*)", ManagedFileHandler, {"path": target_project.path}),
            ])
        handle = self.handlers.pop(0)
        self.handlers.insert(self._handlers_count, handle)

        self.watcher.observe(target_project.path, target_project.muteList)
        if CURRENT_MODE == DEVELOPMENT_MODE:
            self.watcher.observer.schedule(self.watcher, APP_FOLDER, recursive=True)

    def current_project_path(self):
        if not self.project:
            return None
        return self.project.path

    def project_file_changed(self):
        ChangeRequestHandler.broadcast_changes()


if __name__ == "__main__":
    pass

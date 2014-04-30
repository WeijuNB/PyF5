#coding:utf-8
from __future__ import division, print_function, absolute_import

from tornado.web import Application
from tornado import autoreload
from handlers.app import ResourceHandler, DashboardHandler

autoreload.start = lambda: None  # hack to disable autoreload and keep other debug feature intact

from .settings import RESOURCE_FOLDER
from .handlers.api import ProjectAPIHandler, FileSystemAPIHandler, AppAPIHandler
from .handlers.changes import ChangeRequestHandler
from .handlers.project import route_project_request


routes = [
    (r'/_/changes', ChangeRequestHandler),
    (r'/_/api/project/(.*)', ProjectAPIHandler),
    (r'/_/api/fs/(.*)', FileSystemAPIHandler),
    (r'/_/api/app/(.*)', AppAPIHandler),
    (r'/_/?', DashboardHandler),
    (r'/_/(.+)', ResourceHandler, {'path': RESOURCE_FOLDER}),
    (r'/(.*?)', route_project_request),
]

application = Application(
    routes,
    debug=True,
    template_path=RESOURCE_FOLDER
)



# class F5Server(Application):
#     def __init__(self):
#         handlers = [
#             (r"/_/api/changes", ChangeRequestHandler),
#             (r"/_/api/(.*)", APIRequestHandler),
#             (r"/_/(.+)", ResourceHandler, {"path": RESOURCE_FOLDER}),
#             (r"/_/?", RedirectHandler, {'url': '/_/index.html?ver=' + VERSION}),
#             # (r"/", RedirectHandler, {'url': '/_/index.html'}),
#         ]
#         self._handlers_count = len(handlers)
#         settings = {
#             'debug': True,
#             'template_path': RESOURCE_FOLDER,
#             'version': VERSION
#         }
#
#         Application.__init__(self, handlers, ".*$", None, False, **settings)
#
#         if self.active_project:
#             self.load_project(self.active_project)
#
#     @property
#     def watcher(self):
#         if not hasattr(self, '_watcher'):
#             self._watcher = ChangesWatcher(self)
#             for project in self.config.projects:
#                 self._watcher.add_watch(project.path, project.muteList)
#         return self._watcher
#
#     @property
#     def config(self):
#         if not hasattr(self, '_config'):
#             if os.path.exists(CONFIG_PATH):
#                 self._config = Config.load(CONFIG_PATH)
#             else:
#                 self._config = Config()
#                 self._config.path = CONFIG_PATH
#         return self._config
#
#     @property
#     def active_project(self):
#         for project in self.config.projects:
#             if project.active:
#                 return project
#         return None
#
#     def load_project(self, target_project):
#         if not self.find_project(target_project.path):
#             self.config.projects.append(target_project)
#
#         if self.active_project:
#             self.active_project.active = False
#
#         if os.path.exists(target_project.path):
#             target_project.active = True
#         else:
#             target_project.active = False
#             return False
#
#         if len(self.handlers) > 1:
#             self.handlers.pop(-1)
#         if target_project.targetHost:
#             self.add_handlers(".*$", [(r"/(.*)", ForwardRequestHandler)])
#             ForwardRequestHandler.forward_host = target_project.targetHost
#         else:
#             self.add_handlers(".*$", [
#                 (r"/", RedirectHandler, {'url': '/_/index.html?ver=' + VERSION}),
#                 (r"/(.*)", ManagedFileHandler, {"path": target_project.path}),
#             ])
#         handle = self.handlers.pop(0)
#         self.handlers.insert(self._handlers_count, handle)
#
#         self.watcher.add_watch(target_project.path, target_project.muteList)
#         if CURRENT_MODE == DEVELOPMENT_MODE:
#             self.watcher.add_watch(APP_FOLDER)
#
#         print('load_project:', target_project)
#         return True
#
#     def find_project(self, child_path):
#         for project in self.config.projects:
#             if path_is_parent(project.path, child_path):
#                 return project
#         return None
#
#     def current_project_path(self):
#         if not self.active_project:
#             return None
#         return self.active_project.path
#
#     def project_file_changed(self):
#         ChangeRequestHandler.broadcast_changes()



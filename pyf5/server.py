#coding:utf-8
from __future__ import division, print_function, absolute_import
import os

from tornado.web import Application
from tornado import autoreload
from handlers.app import ResourceHandler, DashboardHandler

autoreload.start = lambda: None  # hack to disable autoreload and keep other debug feature intact

from .settings import RESOURCE_FOLDER
from .handlers.api import ProjectAPIHandler, FileSystemAPIHandler, AppAPIHandler
from .handlers.changes import ChangeRequestHandler
from .handlers.project import route_project_request


routes = [
    (r'/(_f5.js)', ResourceHandler, {'path': os.path.join(RESOURCE_FOLDER, 'js')}),
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
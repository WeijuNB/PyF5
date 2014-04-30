import os
from tornado.web import StaticFileHandler, RequestHandler
from settings import RESOURCE_FOLDER


class ResourceHandler(StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class DashboardHandler(RequestHandler):
    def get(self, *args, **kwargs):
        content = open(os.path.join(RESOURCE_FOLDER, 'index.html')).read()
        self.write(content)
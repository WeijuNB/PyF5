import anydbm
import json
import os

from .settings import CONFIG_PATH
from .logger import *


class DictStorage(dict):
    def __init__(self, path):
        dict.__init__(self)
        self.path = path

        if os.path.exists(path):
            content = open(path).read()
            self.update(json.loads(content))

    def flush(self):
        info(self, 'flushing...')
        open(self.path, 'w+').write(json.dumps(self, indent=4))

    def __repr__(self):
        return '[Storage]'


class Config(DictStorage):
    def __init__(self, path):
        DictStorage.__init__(self, path)
        self.setdefault('projects', [])

    def find_project(self, path):
        for project in self['projects']:
            if project['path'] == path:
                return project
        return None


config = Config(CONFIG_PATH)
"""
projects: [
    {
        path: str
        active: bool
        mode: 'static' / 'dynamic'
        host: str,
        port: int,
    }
],
"""


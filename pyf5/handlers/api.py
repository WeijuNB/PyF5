#coding:utf-8
from __future__ import absolute_import, division, print_function
import os
import json
import socket
import time
from functools import partial

from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.web import RequestHandler, asynchronous, os, HTTPError


from ..config import config
from ..settings import VERSION, RESOURCE_FOLDER
from ..utils import normalize_path
from ..logger import *
from .base import BaseRequestHandler


class BaseAPIHandler(BaseRequestHandler):
    def handle(self, path):
        if not path:
            self.default()
        else:
            path = path.replace('.', '_').replace('/', '_')
            if path.startswith('_') or path in dir(BaseRequestHandler):
                raise HTTPError(500, 'ILLEGAL_PATH')
            elif hasattr(self, path):
                data = self.request.arguments
                for key in data:
                    if type(data[key]) == list and len(data[key]) == 1:
                        data[key] = data[key][0]
                if self.request.method == 'POST':
                    try:
                        json_data = json.loads(self.request.body)
                        data.update(json_data)
                    except:
                        pass
                debug(self, '<-', path, data)
                self.__getattribute__(path)(**data)
            else:
                raise HTTPError(404)

    def echo(self, **kwargs):
        self.finish_json(kwargs)


class ProjectAPIHandler(BaseAPIHandler):
    def list(self):
        return self.finish_json(
            config.get('projects', [])
        )

    def add(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if not project:
            config['projects'].append({
                'path': path,
                'mode': 'static'
            })
            if len(config['projects']) == 1:
                config['projects'][0]['active'] = True
            config.flush()
            return self.finish_json({'success': True})
        else:
            return self.finish_json({'error': 'Project Already Existed'})

    def select(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if project:
            for p in config['projects']:
                p['active'] = False
            project['active'] = True
            config.flush()
            self.finish_json({'success': True})
        else:
            self.finish_json({'error': 'Project Not Found'})

    def update(self, path, options):
        path = normalize_path(path)
        project = config.find_project(path)
        if not project:
            return self.finish_json({'error': 'Project Not Found'})

        project.update(options)
        config.flush()
        return self.finish_json({'success': True})

    def remove(self, path):
        path = normalize_path(path)
        project = config.find_project(path)
        if project:
            config['projects'].remove(project)
            config.flush()
            return self.finish_json({'success': True})
        else:
            return self.finish_json({'error': 'Project Not Found'})


class FileSystemAPIHandler(BaseAPIHandler):
    def list(self, path):
        ret = []
        for name in os.listdir(path):
            abs_path = normalize_path(os.path.join(path, name))
            _, ext = os.path.splitext(name)
            is_dir = os.path.isdir(abs_path)

            ret.append({
                'name': name,
                'type': 'DIR' if is_dir else ext.replace('.', '').lower()
            })
        ret.sort(key=lambda x: (x['type'] != 'DIR', name))
        return self.finish_json(ret)

    def save(self, path, content):
        open(path, 'w').write(content.encode('utf-8'))
        return self.finish_json({'success': True})


class AppAPIHandler(BaseAPIHandler):
    def ver(self):
        self.finish_json(VERSION)


'''
class UrlAPI(APIRequestHandler):
    def setup(self):
        pass

    def checkAlive(self):
        url = self.get_argument('url', None)
        if not url:
            return self.respond_error(INVALID_PARAMS, u'缺少url参数')
        self.tryCheckAlive(url)

    def tryCheckAlive(self, url, count=0):
        client = AsyncHTTPClient()
        client.fetch(url, partial(self.checkAliveRespond, url, count), connect_timeout=1, request_timeout=1)

    def checkAliveRespond(self, url, count, response):
        if response.code / 100 in [2, 3]:
            return self.respond_success({})
        elif count > 3:
            return self.respond_error('NOT_ALIVE', u'目标网址不可用')
        else:
            ioloop.IOLoop.instance().add_timeout(time.time() + 1, lambda: self.tryCheckAlive(url, count + 1))
    '''
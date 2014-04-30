#coding:utf-8
import tornado
from tornado import httpclient
from tornado.web import asynchronous, StaticFileHandler, RequestHandler, HTTPError

from ..config import config
from ..logger import error
from .helpers import process_html, process_css


class StaticRequestHandler(StaticFileHandler):
    def __init__(self, application, request, path):
        self.file_path = path
        StaticFileHandler.__init__(self, application, request)

    # noinspection PyMethodOverriding
    def initialize(self):
        StaticFileHandler.initialize(self, self.file_path)

    def set_extra_headers(self, path):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class DynamicRequestHandler(RequestHandler):
    def __init__(self, application, request, host, port):
        RequestHandler.__init__(self, application, request)
        self.host = host
        self.port = port

    @asynchronous
    def get(self, *args, **kwargs):
        def handle_response(response):
            if response.error and not isinstance(response.error, httpclient.HTTPError) \
                    or response.code == 599:
                self.set_status(500)

                self.write(''.join([
                    '<html><head><meta charset="utf8">',
                    '<script>',
                    'setTimeout(function() { location.reload(); }, 1000);',
                    '</script>',
                    '</head><body>',
                    '源服务器错误：<br>',
                    str(response.error),
                    response.body or '',
                    '<p>正在为您自动重试...</p>',
                    '</body></html>',
                ]))
                self.finish()
            else:
                self.set_status(response.code)
                for header in response.headers:
                    if header not in [
                        'Transfer-Encoding',  # 防止 chunked
                        'Content-Encoding', 'Content-Length',  # 防止gzip
                        'Etag', 'Expires', 'Last-Modified',  # 防止缓存
                        'Set-Cookie'  # 后面cookie会另外处理
                    ]:
                        self.set_header(header, response.headers.get(header))

                    # 防止缓存
                    self.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.set_header('Pragma', 'no-cache')
                    self.set_header('Expires', '0')

                    # 多个Set-Cookie会在response.headers中被合并，这还原成多个Set-Cookie
                    if header == 'Set-Cookie':
                        raw_cookie_list = response.headers.get_list(header)
                        if len(raw_cookie_list) == 1:
                            self.set_header('Set-Cookie', response.headers.get(header))
                        elif len(raw_cookie_list) > 1:
                            for raw_cookie in raw_cookie_list:
                                self.add_header('Set-Cookie', raw_cookie)

                if response.body:
                    content_type = response.headers.get('Content-Type', '')
                    if content_type and 'text/html' in content_type:
                        body = process_html(response.body)
                    elif content_type and 'text/css' in content_type:
                        body = process_css(response.body)
                    else:
                        body = response.body

                    self.set_header('Content-Length', len(body))
                    self.write(body)
                self.finish()

        headers = self.request.headers
        headers['Host'] = self.host

        for key in ['If-Modified-Since', 'If-None-Match', 'Expires', 'Cache-Control']:
            if key in headers:
                del headers[key]

        url = 'http://%s:%s%s' % (self.host, self.port, self.request.uri)
        req = tornado.httpclient.HTTPRequest(url=url,
                                             method=self.request.method,
                                             body=self.request.body,
                                             request_timeout=99999,
                                             headers=headers,
                                             follow_redirects=False,
                                             allow_nonstandard_methods=True)

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            client.fetch(req, handle_response)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                error(self, 'no respond')
                raise HTTPError(500, 'No Respond:' + url)

    @asynchronous
    def post(self, *args, **kwargs):
        self.get()


# todo: add reloader.js
def route_project_request(application, request):
    project = config.current_project()
    if project['mode'] == 'static':
        path = project['path']
        handler = StaticRequestHandler(application, request, path)
    else:
        host = project['host']
        port = project.get('port') or 80
        handler = DynamicRequestHandler(application, request, host, port)
    return handler
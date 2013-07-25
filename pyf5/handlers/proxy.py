#coding:utf-8
import Cookie
import tornado
import tornado.httpclient
from tornado.web import asynchronous

from pyf5.settings import RELOADER_TAG


class ForwardRequestHandler(tornado.web.RequestHandler):
    forward_host = None

    @asynchronous
    def get(self, *args, **kwargs):
        def handle_response(response):
            if response.error and not isinstance(response.error, tornado.httpclient.HTTPError) \
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
                    # 防止gzip
                    if header not in ['Content-Encoding', 'Content-Length']:
                        self.set_header(header, response.headers.get(header))

                    # 多个Set-Cookie会在response.headers中被合并，这还原成多个Set-Cookie
                    if header == 'Set-Cookie':
                        raw_cookie_list = response.headers.get_list(header)
                        if len(raw_cookie_list) == 1:
                            self.set_header('Set-Cookie', response.headers.get(header))
                        elif len(raw_cookie_list) > 1:
                            if not hasattr(self, "_new_cookie"):
                                self._new_cookie = Cookie.SimpleCookie()
                                for raw_cookie in raw_cookie_list:
                                    self._new_cookie.load(raw_cookie)

                if response.body:
                    content_type = response.headers.get('Content-Type', '')
                    if content_type and 'text/html' in content_type:
                        body = response.body.replace('</body>', RELOADER_TAG + '\n</body>')
                    else:
                        body = response.body

                    self.set_header('Content-Length', len(body))
                    self.write(body)
                self.finish()

        headers = self.request.headers
        headers['Host'] = self.forward_host

        for key in ['If-Modified-Since', 'If-None-Match']:
            if key in headers:
                del headers[key]

        req = tornado.httpclient.HTTPRequest(url='http://%s%s' % (self.forward_host, self.request.uri),
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
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @asynchronous
    def post(self, *args, **kwargs):
        self.get()

#coding:utf-8
import tornado
import tornado.httpclient
from tornado.web import asynchronous


class ForwardRequestHandler(tornado.web.RequestHandler):
    forward_host = None

    @asynchronous
    def get(self, *args, **kwargs):
        def handle_response(response):
            if response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
                self.finish()
            else:
                self.set_status(response.code)
                for header in response.headers:
                    if header not in ['Content-Encoding', 'Content-Length']:  # 防止gzip
                        self.set_header(header, response.headers.get(header))

                if response.body:
                    content_type = response.headers.get('Content-Type', '')
                    if content_type and 'text/html' in content_type:
                        body = response.body.replace('</body>', '<script id="_f5_script" src="/_/js/reloader.js"></script>\n</body>')
                    else:
                        body = response.body

                    self.set_header('Content-Length', len(body))
                    self.write(body)
                self.finish()

        headers = self.request.headers
        headers['Host'] = self.forward_host

        req = tornado.httpclient.HTTPRequest(url='http://%s%s' % (self.forward_host, self.request.uri),
                                             method=self.request.method,
                                             body=self.request.body,
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

import tornado.ioloop
import tornado.web
from tornado.web import RequestHandler, StaticFileHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class TemplateHandler(RequestHandler):
    def get(self, file=None):
        if file is None:
            file = 'UI'

        self.render('%s.html' % file, active=file)


def make_app():
    return tornado.web.Application([
        (r"/", TemplateHandler),
        (r"/tool/(.*)", TemplateHandler),
        (r"/static/(.*)", StaticFileHandler, {"path": "./static/"}),
    ], template_path='./templates', debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print "Starting server - port: 8888 "
    tornado.ioloop.IOLoop.current().start()

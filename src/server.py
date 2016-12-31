# -*- coding: utf8 -*-

from __future__ import unicode_literals

import tornado.ioloop
import tornado.web
from tornado.web import RequestHandler, StaticFileHandler

from algorithms import Algorithms
from problems import Problems
from inspectors import Inspectors
from agent import Agent
from agentTrainingHandler import AgentTrainingHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class TemplateHandler(RequestHandler):
    def renderTrain(self):
        def mapper(classes, attr):
            return {
                cls.__name__: getattr(cls, attr)
                for cls in classes
            }

        self.render(
            'train.html',
            active='train', algorithms=Algorithms.keys(),
            algorithmsDescription=mapper(Algorithms.values(), '__doc__'),
            algorithmsDomain=mapper(Algorithms.values(), 'DOMAIN'),
            algorithmsParams=mapper(Algorithms.values(), 'PARAMS'),
            algorithmsParamsDefault=mapper(Algorithms.values(), 'PARAMS_DEFAULT'),
            algorithmsParamsDomain=mapper(Algorithms.values(), 'PARAMS_DOMAIN'),
            algorithmsParamsDescription=mapper(Algorithms.values(), 'PARAMS_DESCRIPTION'),
            problems=Problems.keys(),
            problemsDescription=mapper(Problems.values(), '__doc__'),
            problemsDomain=mapper(Problems.values(), 'DOMAIN'),
            problemsParams=mapper(Problems.values(), 'PARAMS'),
            problemsParamsDefault=mapper(Problems.values(), 'PARAMS_DEFAULT'),
            problemsParamsDomain=mapper(Problems.values(), 'PARAMS_DOMAIN'),
            problemsParamsDescription=mapper(Problems.values(), 'PARAMS_DESCRIPTION'),
            inspectors=Inspectors.keys(),
            inspectorsDescription=mapper(Inspectors.values(), '__doc__'),
            inspectorsParams=mapper(Inspectors.values(), 'PARAMS'),
            inspectorsParamsDefault=mapper(Inspectors.values(), 'PARAMS_DEFAULT'),
            inspectorsParamsDomain=mapper(Inspectors.values(), 'PARAMS_DOMAIN'),
            inspectorsParamsDescription=mapper(Inspectors.values(), 'PARAMS_DESCRIPTION'),
            agentParams=Agent.PARAMS,
            agentParamsDefault=Agent.PARAMS_DEFAULT,
            agentParamsDomain=Agent.PARAMS_DOMAIN,
            agentParamsDescription=Agent.PARAMS_DESCRIPTION
        )

    def get(self, file=None):
        if file is None:
            file = 'train'

        spec = {
            'train': self.renderTrain,
            'train/': self.renderTrain
        }

        if file in spec:
            return spec[file]()

        self.render(
            '%s.html' % file, active=file)


def make_app():
    return tornado.web.Application([
        (r"/", TemplateHandler),
        (r"/tool/(.*)/?", TemplateHandler),
        (r"/static/(.*)/?", StaticFileHandler, {"path": "./static/"}),
        (r"/subscribe/train/?", AgentTrainingHandler)
    ], template_path='./templates', debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print "Starting server - port: 8888 "
    tornado.ioloop.IOLoop.current().start()

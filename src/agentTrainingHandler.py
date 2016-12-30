# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json

from tornado.websocket import WebSocketHandler
from tornado.web import HTTPError
from tornado.ioloop import PeriodicCallback

from algorithms import Algorithms
from problems import Problems
from agent import Agent
import utils


class AgentTrainingHandler(WebSocketHandler):
    """
    Replies on the websocket connection /subscribe/train
    All inbound messages expect the field 'command' to be defined, as well as
    any other field the command would expect (see the corresponding function
    documentation)
    Outbound messages will have a structure that is specific to the command.
    See the command's corresponding function's documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        super(AgentTrainingHandler, self).__init__(*args, **kwargs)
        # the agent the user is currently working on
        self._agent = Agent()
        self._currentTrain = None
        self._currentTest = None
        self._execPeriodicCallback = None
        self._progress = None

    def open(self):
        print("WebSocket opened")

    def _testingDone(self):
        if self._execPeriodicCallback is not None:
            self._execPeriodicCallback.stop()
        self._execPeriodicCallback = None
        self._currentTrain = None

    def nextTestStep(self):
        if self._currentTest is None or self._execPeriodicCallback is None:
            return
        try:
            accReturn, iStep, done = self._currentTest.next()
            if done:
                print "Testing Finished. Return=%d." % (accReturn)
        except StopIteration:
            self._testingDone()

    def _trainingDone(self):
        if self._execPeriodicCallback is not None:
            self._execPeriodicCallback.stop()
        self._execPeriodicCallback = None
        self._currentTrain = None

        # run one more episode after training with rendering enabled
        print "Episode %d - Final test." % (self._agent.nEpisodes)
        self._currentTest = self._agent.test()
        if self._agent.delay == 0:
            for r, iE, done in self._currentTest:
                if done:
                    print "Testing Finished. Return=%d" % (r)
            return self._testingDone()
        self._execPeriodicCallback = PeriodicCallback(
            self.nextTestStep, self._agent.delay)
        self._execPeriodicCallback.start()

    def _trainingProgress(self, pcVal, c, m, episodeReturn):
        print "Training progress: %.1f%% (episode %d/%d) - return=%d" % (
            float(pcVal) / 10, c, m, episodeReturn)

    def _nextTrainStep(self):
        if self._currentTrain is None or self._execPeriodicCallback is None:
            return
        try:
            accReturn, iEpisode, iStep, done = self._currentTrain.next()
            if done:
                # print "Training progress: episode %d/%d, return=%d" % (
                #     iEpisode, self._agent.nEpisodes, accReturn)
                self._progress(
                    iEpisode, self._agent.nEpisodes, episodeReturn=accReturn)
        except StopIteration:
            self._trainingDone()

    def _trainCommand(self, message):
        """
        Called when receiving the command 'train'
        Message expects the fields.subfields:
        * algorithm.name: name of the algorithm to use for training
        * algorithm.params: hyperparameter settings for this algorithm
          (param name - param value mapping)
        * problem.name: name of the problem to solve
        * problem.params: hyperparameters settings for this problem
          (param name - param value mapping)
        * agent.params: agent's execution parameters
        """
        algo = Algorithms[message['algorithm']['name']](
            **message['algorithm']['params'])
        problem = Problems[message['problem']['name']](
            **message['problem']['params'])

        # create a new agent. The agent will be setup on a new problem and will
        # solve using a new algorithm, but defined inspectors remain the same.
        # They will be setup for the new problem and algorithm later on.
        self._agent = Agent(
            # reuse inspectors setup on previous agent.
            inspectors=self._agent.inspectors,
            **message['agent']['params'])

        self._agent.setup(problem, algo)

        self._currentTrain = self._agent.train()

        self._progress = utils.makeProgress(0, 1000, self._trainingProgress)

        if self._agent.delay == 0:
            for r, iE, iS, done in self._currentTrain:
                if done:
                    self._progress(iE, self._agent.nEpisodes, episodeReturn=r)
            return self._trainingDone()
        self._execPeriodicCallback = PeriodicCallback(
            self._nextTrainStep, self._agent.delay)
        self._execPeriodicCallback.start()

    def on_message(self, message):
        message = json.loads(message)

        commands = {
            'train': self._trainCommand
        }

        if message.get('command') in commands:
            return commands[message.get('command')](message)

        raise HTTPError("Unknown command: %s" % str(commands.get('command')))

    def on_close(self):
        print("WebSocket closed")

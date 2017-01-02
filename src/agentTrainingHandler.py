# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json

from tornado.websocket import WebSocketHandler
from tornado.web import HTTPError
from tornado.ioloop import PeriodicCallback

from algorithms import Algorithms
from problems import Problems
from agent import Agent
from inspectors.factory import InspectorsFactory


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

        self._inspectorsFactory = InspectorsFactory(self.write_message)

    def open(self):
        print("WebSocket opened")

    #############################################
    # TRAIN COMMAND SUB-ROUTINES
    #############################################
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

    def _nextTrainStep(self):
        if self._currentTrain is None or self._execPeriodicCallback is None:
            return
        try:
            accReturn, iEpisode, iStep, done = self._currentTrain.next()
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
        if self._agent is not None:
            self._agent.release()
        self._agent = Agent(
            # reuse inspectors setup on previous agent.
            inspectorsFactory=self._inspectorsFactory,
            **message['agent']['params'])

        self._agent.setup(problem, algo)
        self._inspectorsFactory.setup(problem, algo, self._agent)

        self._currentTrain = self._agent.train()

        if self._agent.delay == 0:
            for r, iE, iS, done in self._currentTrain:
                continue
            return self._trainingDone()
        self._execPeriodicCallback = PeriodicCallback(
            self._nextTrainStep, self._agent.delay)
        self._execPeriodicCallback.start()

    def _registerInspectorCommand(self, message):
        """
        Called when receiving the command 'registerInspector'
        Message expects to hold the fields.subfields:
        * name: name of the inspector to register
        * uid: uid for this inspector - will be transmitted with each message
          sent by the created inspector instance.
        * params; override parameter settings for the created inspector as a
          mapping between parameter name and value.
          None should be required (they all have a default value but it might
          not be suited to the problem & algorithm the agent is running).
          See the inspector class doc for more details about these.
        """
        self._inspectorsFactory.registerInspector(
            message['name'], message['uid'], message.get('params', {}))

    def on_message(self, message):
        """
        All messages should at least hold the field 'command' plus any other
        field required by the given command. See the corresponding command
        function for more detail about these.
        """
        message = json.loads(message)

        commands = {
            'train': self._trainCommand,
            'registerInspector': self._registerInspectorCommand
        }

        if message.get('command') in commands:
            print "[AgentTraining] Executing command: %s" % (
                message.get('command'))
            return commands[message.get('command')](message)

        raise HTTPError("Unknown command: %s" % str(commands.get('command')))

    def on_close(self):
        print("WebSocket closed")

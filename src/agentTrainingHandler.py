# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import time
import logging

from tornado.websocket import WebSocketHandler
from tornado.web import HTTPError
from tornado.ioloop import PeriodicCallback, IOLoop

import utils
from algorithms import Algorithms
from problems import Problems
from agent import Agent
from inspectors.factory import InspectorsFactory


def placeholder():
    pass


class DelayedExecution(object):
    """
    Wraps up the code that enables to execute the agent in a delayed fashion.
    This will use the agent's `stepDelay` and `episodeDelay` to setup timeouts
    and callbacks. Beware that an agent setup with 0 delay in both cases will
    block the server thread during the entirety of its training of testing
    execution.
    """
    def __init__(self, agent, hooks, action='train'):
        """
        Initialize the delayed execution on the given agent.
        `hooks` can contain the following keys associated with callbacks:
        * `execFinished`: called once the execution is terminated
        * `step`: called at every step
        * `episodeFinished`: called after each episode
        The `action` parameter denotes the kind of run performed. `train` will
        train the agent, `test` (or any other value) will run a single test
        episode.
        """
        super(DelayedExecution, self).__init__()
        self._agent = agent
        self._hooks = hooks
        self._action = action

        self._hookExecFinished = self._hooks.get('execFinished', placeholder)
        self._hookStep = self._hooks.get('step', placeholder)
        self._hookEpisodeFinished = self._hooks.get(
            'episodeFinished', placeholder)

        self._currentExec = None

        self._execPeriodicCallback = None

        self._interrupted = False

        print(
            "Delayed callback setup - episodeDelay =", self._agent.episodeDelay,
            " - stepDelay =", self._agent.stepDelay)

    def interrupt(self):
        self._interrupted = True
        self._execFinished()

    def _execFinished(self):
        self._currentExec = None
        if self._execPeriodicCallback:
            self._execPeriodicCallback.stop()
            self._execPeriodicCallback = None
        self._hookExecFinished()

    def _onStep(self):
        if self._interrupted:
            print "onStep: Interrupted execution"
            return

        if self._currentExec is None or self._execPeriodicCallback is None:
            return

        try:
            accReturn, iEpisode, iStep, done = self._currentExec.next()
            self._hookStep()
            if done:
                self._onEpisodeEnd()
        except StopIteration:
            self._execFinished()

    def _onEpisodeEnd(self):
        self._hookEpisodeFinished()
        if self._interrupted:
            print "onEpisodeEnd: Interrupted execution"
            return

        if self._execPeriodicCallback:
            self._execPeriodicCallback.stop()

        # it is assumed that at this point, at least the step or episode is
        # delayed (and if the step is delayed, adding a 0ms delay to the
        # episode won't be noticeable.)
        IOLoop.current().call_later(
            float(self._agent.episodeDelay) / 1000.0,
            self._startEpisode)

    def _startEpisode(self):
        if self._interrupted:
            print "startEpisode: Interrupted execution"
            return

        if self._currentExec is None:
            return

        canGoQuick = (
            self._agent.stepDelay == 0 and not self._agent.shouldRender())
        canGoQuick |= (
            self._agent.renderStepDelay == 0 and self._agent.shouldRender())
        if canGoQuick:
            for r, iE, iS, done in self._currentExec:
                if done:
                    self._onEpisodeEnd()
                    break  # a new episode will be scheduled
            else:  # the execution is finished
                self._execFinished()
        else:
            # stop just in case, better twice than none
            if self._execPeriodicCallback is not None:
                self._execPeriodicCallback.stop()

            # setup the callback for this episode
            # is it costly to re-create one at each episode?
            if self._agent.shouldRender():
                self._execPeriodicCallback = PeriodicCallback(
                    self._onStep, self._agent.renderStepDelay)
            else:
                self._execPeriodicCallback = PeriodicCallback(
                    self._onStep, self._agent.stepDelay)

            self._execPeriodicCallback.start()

    def _runUndelayed(self):
        """
        Used when no delay at all is setup to speed up stuff and avoid
        infinite recursion.
        """
        for r, iE, iS, done in self._currentExec:
            self._hookStep()
            if done:
                self._hookEpisodeFinished()

        self._execFinished()

    def run(self):
        self._interrupted = False
        if self._action == 'train':
            self._currentExec = self._agent.train()
        else:
            self._currentExec = self._agent.test()

        if all(v == 0 for v in [
                self._agent.episodeDelay,
                self._agent.stepDelay,
                self._agent.renderStepDelay]):
            self._runUndelayed()
        else:
            self._startEpisode()


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
        self._trainStartT = None

        self._inspectorsFactory = InspectorsFactory(self.write_message)

        self._exec = None

    def open(self):
        print("WebSocket opened")

    #############################################
    # TRAIN COMMAND SUB-ROUTINES
    #############################################
    def _testingDone(self):
        self._exec = None
        if not self._agent.isSetup:
            return self.write_message({
                'route': 'success',
                'message': ("Successfull interruption, but no agent training "
                            "was in progress.")
            })

        self.write_message({
            'route': 'success',
            'message': "Agent successfully trained in %s" % utils.timeFormat(
                time.time() - (self._trainStartT or time.time()))
        })

    def _trainingDone(self):
        # run one more episode after training with rendering enabled
        if not self._agent.isSetup:
            return self.write_message({
                'route': 'success',
                'message': ("Successfull interruption, but no agent training "
                            "was in progress.")
            })

        print "Episode %d - Final test." % (self._agent.nEpisodes)

        self._exec = DelayedExecution(self._agent, {
            'execFinished': self._testingDone
        }, action='test')
        self._exec.run()

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
        self._trainStartT = time.time()
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

        self._exec = DelayedExecution(self._agent, {
            'execFinished': self._trainingDone
        }, action='train')
        self._exec.run()

    def _interruptCommand(self, message):
        """
        Called when receiving the command 'interrupt'.
        No specific parameter is expected. This interrupts the current agent
        training process.
        If no agent training is currently in progress, this will do nothing.
        """
        if self._exec is not None:
            self._exec.interrupt()

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
            'registerInspector': self._registerInspectorCommand,
            'interrupt': self._interruptCommand
        }

        if message.get('command') in commands:
            print "[AgentTraining] Executing command: %s" % (
                message.get('command'))
            try:
                return commands[message.get('command')](message)
            except Exception as e:
                logging.exception(e)
                return self.write_message({
                    'route': 'error',
                    'message': str(e)
                })

        raise HTTPError(404, "Unknown command: %s"
                        % message.get('command', 'undefined'))

    def on_close(self):
        print("WebSocket closed")

# -*- coding: utf8 -*-

from __future__ import unicode_literals

import time
import logging
logger = logging.getLogger(__name__)

from parametizable import Parametizable
from consts import ParamsTypes, Spaces, Hooks


class AgentException(Exception):
        pass


class Agent(Parametizable):
    """Run and execute a given algorithm in the given environment."""
    PARAMS = {
        'nEpisodes': ParamsTypes.Number,
        'renderFreq': ParamsTypes.Number,
        'stepDelay': ParamsTypes.Number,
        'episodeDelay': ParamsTypes.Number,
        'renderStepDelay': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'nEpisodes': {
            'range': (0, float('inf')),
            'values': [10, 100, 1000, 10000, 100000]
        },
        'renderFreq': {
            'range': (-1, float('inf')),
            'values': ['testOnly', -1, 10, 100, 1000, 2000, 10000]
        },
        'stepDelay': {
            'range': (0, 10000),
            'values': [0, 1, 100]
        },
        'renderStepDelay': {
            'range': (0, 10000),
            'values': [0, 1, 100, 1000]
        },
        'episodeDelay': {
            'range': (0, 10000),
            'values': [0, 1, 100]
        }
    }

    PARAMS_DEFAULT = {
        'nEpisodes': 2500,
        'renderFreq': 500,
        'stepDelay': 0,
        'episodeDelay': 1,
        'renderStepDelay': 0
    }

    PARAMS_DESCRIPTION = {
        'nEpisodes': "\
Number of episodes one run of the training will last unless manually \
interrupted.",
        'renderFreq': "\
If the environment has rendering capabilities, this is the frequency with which\
 a rendered episode should happen. Rendering is done server-side. \
Set to -1 to disable.",
        'stepDelay': "\
Delay in ms between steps. Set to 0 will disable delaying.",
        'renderStepDelay': "Delay in ms between steps while rendering.",
        'episodeDelay': "\
Delay in ms between episodes. Set to 0 will disable delaying. Note that server \
will only reply to requests during delays."
    }

    def __init__(self, inspectorsFactory=None, **kwargs):
        super(Agent, self).__init__(**kwargs)

        self._problem = None
        self._algo = None
        self._inspectorsFactory = inspectorsFactory or []

        self.isSetup = False
        self._minDuration = float('inf')
        self._iEpisode = 0
        self._isTesting = False

    def _checkCompatibility(self, problem, algo):
        """
        Make sure the algo can solve the given problem.
        This simply validate domains compatibility. Continuous domain
        algorithms can solve discrete problems, but discrete domain
        algorithms cannot solve continuout problems.
        """
        for space in ('state', 'action'):
            if problem.DOMAIN[space] == Spaces.Continuous:
                if algo.DOMAIN[space] == Spaces.Discrete:
                    # incompatibility
                    raise AgentException(
                        "Incompatible %s space: %s algorithms cannot solve %s "
                        "problem." % (space, algo.DOMAIN[space],
                                      problem.DOMAIN[space]))

    def setup(self, problem, algo):
        logger.info(
            "Agent setup: Algorithm=%s, Problem=%s",
            algo.__class__.__name__,
            problem.__class__.__name__)
        self._checkCompatibility(problem, algo)
        self._problem = problem
        self._algo = algo

        self._problem.setup()
        self._algo.setup(self._problem)

        self.isSetup = True

    def test(self):
        """
        Returns an iterator that will run a single episode of the environment.
        It will yield the accumulated reward, the step number and a boolean
        indicating whether the episode is terminated.
        If rendering wasn't specifically disabled, the episode will be rendered.
        """
        self._isTesting = True
        state = self._problem.reset()
        action = self._algo.pickAction(
            state, self.nEpisodes, optimize=True)
        episodeReturn = 0
        startT = time.time()
        iStep = 0
        didRender = False

        self._algo.startEpisode(state)

        for iStep in xrange(self._problem.maxSteps):
            newState, reward, _, info = self._problem.step(action)
            episodeReturn += reward

            # no training this time
            action = self._algo.pickAction(
                newState, self.nEpisodes, optimize=True)

            state = newState

            if self.renderFreq != -1:
                didRender = True
                self._problem.render()

            done = self._problem.episodeDone(stepI=iStep)

            yield episodeReturn, self.nEpisodes, iStep, done or (
                iStep == self._problem.maxSteps - 1)

            if done:
                break

        if didRender:
            self._problem.render(close=True)

        duration = time.time() - startT
        self._minDuration = min(self._minDuration, duration)

        yield (episodeReturn, self.nEpisodes, self._problem.maxSteps, True)

        self._inspectorsFactory.dispatch(
            hook=Hooks.trainingProgress,
            iEpisode=self.nEpisodes,
            nEpisodes=self.nEpisodes,
            episodeReturn=episodeReturn,
            episodeSteps=iStep,
            episodeDuration=duration if not didRender else self._minDuration)
        self._isTesting = False

    def shouldRender(self):
        # render if we are in testing and the renderFreq isn't -1
        shouldRender = self._isTesting and self.renderFreq != -1
        # or, alternatively, render if renderFreq is neither -1 nor 'testOnly'
        # AND it is either 0 or the module of renderFreq is 0
        shouldRender |= (
            self.renderFreq != -1 and self.renderFreq != 'testOnly' and
            (self.renderFreq == 0 or (
                self.renderFreq > 0 and
                (self._iEpisode - 1) % self.renderFreq == 0)))
        return shouldRender

    def train(self):
        """
        Returns an iterator that will execute one step of the environment
        each time its next() function is called.
        After each step it yields the return for the episode (so far),
        the episode number, the step number and a boolean indicating whether
        the episode is terminated.
        Use inspectors and associated hook functions to gather more
        information about the execution of the environment.
        """
        for self._iEpisode in xrange(0, self.nEpisodes):
            startT = time.time()
            timeSpentRendering = 0
            state = self._problem.reset()
            action = self._algo.pickAction(state, self._iEpisode)
            episodeReturn = 0
            didRender = False

            self._algo.startEpisode(state)

            for iStep in xrange(self._problem.maxSteps):
                shouldRender = self.shouldRender()

                newState, reward, _, info = self._problem.step(action)
                episodeReturn += reward

                action = self._algo.train(
                    oldState=state,
                    newState=newState,
                    action=action,
                    reward=reward,
                    episodeI=self._iEpisode,
                    stepI=iStep)

                state = newState

                if shouldRender:
                    self._problem.render()

                done = self._problem.episodeDone(stepI=iStep)

                yield episodeReturn, self._iEpisode, iStep, False

                if done:
                    if shouldRender:
                        self._problem.render(close=True)
                    break

            duration = time.time() - startT - timeSpentRendering
            self._minDuration = min(self._minDuration, duration)
            yield (episodeReturn, self._iEpisode, iStep, True)

            self._algo.endEpisode(totalReturn=episodeReturn)
            self._inspectorsFactory.dispatch(
                hook=Hooks.trainingProgress,
                iEpisode=self._iEpisode,
                nEpisodes=self.nEpisodes,
                episodeReturn=episodeReturn,
                episodeSteps=iStep,
                episodeDuration=(
                    duration if not didRender else self._minDuration))

    def release(self):
        """
        Release handles and memory before deletion.
        Used notably to close opened windows server-side.
        """
        if self._problem is not None:
            self._problem.terminate()
            self._problem.release()
            if self.renderFreq != -1:
                self._problem.render(close=True)

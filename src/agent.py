# -*- coding: utf8 -*-

from __future__ import unicode_literals

import time

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
        'episodeDelay': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'nEpisodes': {
            'range': (0, float('inf')),
            'values': [1000, 10000, 100000]
        },
        'renderFreq': {
            'range': (-1, float('inf')),
            'values': [-1, 10, 1000, 2000, 10000]
        },
        'stepDelay': {
            'range': (0, 10000),
            'values': [0, 1, 100]
        },
        'episodeDelay': {
            'range': (0, 10000),
            'values': [0, 1, 100]
        }
    }

    PARAMS_DEFAULT = {
        'nEpisodes': 10000,
        'renderFreq': 2000,
        'stepDelay': 0,
        'episodeDelay': 1
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
        state = self._problem.reset()
        action = self._algo.pickAction(
            state, self.nEpisodes, optimize=True)
        episodeReturn = 0
        startT = time.time()
        iStep = 0
        didRender = False

        self._algo.startEpisode(state)

        for iStep in xrange(self._problem.maxSteps):
            if self.renderFreq != -1:
                didRender = True
                self._problem.render()

            newState, reward, _, info = self._problem.step(action)
            episodeReturn += reward

            # no training this time
            action = self._algo.pickAction(
                newState, self.nEpisodes, optimize=True)

            state = newState

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
            Hooks.trainingProgress, self.nEpisodes,
            self.nEpisodes, episodeReturn, iStep,
            duration if not didRender else 0)

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
        for iEpisode in xrange(0, self.nEpisodes):
            startT = time.time()
            timeSpentRendering = 0
            state = self._problem.reset()
            action = self._algo.pickAction(state, iEpisode)
            episodeReturn = 0
            didRender = False

            self._algo.startEpisode(state)

            for iStep in xrange(self._problem.maxSteps):
                shouldRender = (
                    self.renderFreq != -1 and (
                        self.renderFreq == 0 or (
                            self.renderFreq > 0 and
                            (iEpisode - 1) % self.renderFreq == 0)))

                newState, reward, _, info = self._problem.step(action)
                episodeReturn += reward

                action = self._algo.train(
                    oldState=state,
                    newState=newState,
                    action=action,
                    reward=reward,
                    episodeI=iEpisode,
                    stepI=iStep)

                state = newState

                if shouldRender:
                    self._problem.render()

                done = self._problem.episodeDone(stepI=iStep)

                yield episodeReturn, iEpisode, iStep, done or (
                    iStep == self._problem.maxSteps - 1)

                if done and shouldRender:
                    self._problem.render(close=True)
                    break

            duration = time.time() - startT - timeSpentRendering
            self._minDuration = min(self._minDuration, duration)
            yield (episodeReturn, iEpisode, iStep, True)

            self._algo.endEpisode(totalReturn=episodeReturn)
            self._inspectorsFactory.dispatch(
                Hooks.trainingProgress, iEpisode, self.nEpisodes,
                episodeReturn, iStep, duration if not didRender else 0)

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

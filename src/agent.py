# -*- coding: utf8 -*-

from __future__ import unicode_literals

from parametizable import Parametizable
from consts import ParamsTypes, Spaces


class AgentException(Exception):
        pass


class Agent(Parametizable):
    """Run and execute a given algorithm in the given environment."""
    PARAMS = {
        'nEpisodes': ParamsTypes.Number,
        'renderFreq': ParamsTypes.Number,
        'delay': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'nEpisodes': {
            'range': (0, float('inf')),
            'values': [1000, 10000, 100000]
        },
        'renderFreq': {
            'range': (-1, float('inf')),
            'values': [-1, 10, 1000, 10000]
        },
        'delay': {
            'range': (0, 1000),
            'values': [0, 1, 100]
        }
    }

    PARAMS_DEFAULT = {
        'nEpisodes': 10000,
        'renderFreq': 10000,
        'delay': 0
    }

    PARAMS_DESCRIPTION = {
        'nEpisodes': "\
Number of episodes one run of the training will last unless manually \
interrupted.",
        'renderFreq': "\
If the environment has rendering capabilities, this is the frequency with which\
 a rendered episode should happen. Rendering is done server-side. \
Set to -1 to disable.",
        'delay': "\
Delay in ms between steps. Set to 0 to disable delaying as well as \
adding inspectors during training"
    }

    def __init__(self, inspectors=None, **kwargs):
        super(Agent, self).__init__(**kwargs)

        self._problem = None
        self._algo = None
        self._inspectors = inspectors or []

    @property
    def inspectors(self):
        return self._inspectors

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
        kwargs = {}
        if self._problem.DOMAIN['state'] == Spaces.Discrete:
            kwargs['allStates'] = range(self._problem.env.observation_space.n)
        if self._problem.DOMAIN['action'] == Spaces.Discrete:
            kwargs['allActions'] = range(self._problem.env.action_space.n)
        kwargs['observationSpace'] = self._problem.env.observation_space
        kwargs['actionSpace'] = self._problem.env.action_space
        # TODO: add more parameters to the setup function depending on
        # the needs of algorithms

        self._algo.setup(**kwargs)

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

        self._algo.startEpisode(state)

        # yield episodeReturn, 0, True

        for iStep in xrange(self._problem.maxSteps):
            if self.renderFreq != -1:
                self._problem.render()

            newState, reward, _, info = self._problem.step(action)
            episodeReturn += reward

            # no training this time
            action = self._algo.pickAction(
                newState, self.nEpisodes, optimize=True)

            state = newState

            done = self._problem.episodeDone(stepI=iStep)

            # yield episodeReturn, iStep, done or (
            #     iStep == self._problem.maxSteps - 1)

            if done:
                break

        if self.renderFreq != -1:
            self._problem.render()

        yield episodeReturn, self._problem.maxSteps, True

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
            state = self._problem.reset()
            action = self._algo.pickAction(state, iEpisode)
            episodeReturn = 0

            self._algo.startEpisode(state)

            for iStep in xrange(self._problem.maxSteps):
                if self.renderFreq != -1:
                    if self.renderFreq == 0 or (
                            self.renderFreq > 0 and
                            (iEpisode) % self.renderFreq == 0):
                        self._problem.render()

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

                done = self._problem.episodeDone(stepI=iStep)

                if done:
                    break

            yield episodeReturn, iEpisode, self._problem.maxSteps, True
            self._algo.endEpisode(totalReturn=episodeReturn)

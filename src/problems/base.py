# -*- coding: utf8 -*-

from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

import gym
from parametizable import Parametizable
from consts import ParamsTypes, Spaces


class ProblemException(Exception):
    pass


class BaseProblem(Parametizable):
    """
    Mostly a wrapper around gym's environment, but also provide additional
    parameters and statistics to play with.
    The class is setup for a default behaviour on any gym's environment. When
    subclassing, part of the job should already be done by setting up the
    right parameters. Additional specific behavior can be obtained by overriding
    the functions but care should be taken to call the parent's corresponding
    method using `super(<Class>, self)`
    """
    # These will be or-ed at each step to know whether the environment
    # considers the episode terminated
    EPISODE_TERMINATION_CRITERIA = [
        lambda self, **kwargs: self._done,
        lambda self, stepI, **kwargs: stepI >= self.maxSteps
    ]

    PARAMS = {
        'maxSteps': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'maxSteps': {
            'range': (-1, float('inf')),
            'values': [100, 500, 1000]
        },
    }

    PARAMS_DEFAULT = {
        'maxSteps': 500
    }

    PARAMS_DESCRIPTION = {
        'maxSteps': "Maximum number of steps per episode. Set to -1 to disable."
    }

    # Override to specify a Gym environment that should be loaded.
    GYM_ENVIRONMENT_NAME = None

    # Override to specify compatible algorithm
    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Discrete
    }

    # optional: override to give a specific name to each action
    # action space is assumed to be discrete and 1 dimensional.
    # first action should be in first position, second action in second,
    # and so on.
    ACTION_NAMES = []

    # optional: override to give a specific name to each dimension of
    # the state space. List should be in the same order of the dimensions
    # of the state space (dimension 1 in first position, etc...)
    STATE_DIMENSION_NAMES = []

    def __init__(self, **kwargs):
        super(BaseProblem, self).__init__(**kwargs)
        self._done = False
        self._env = None
        self.observationSpace = None
        self.actionSpace = None

    @property
    def env(self):
        return self._env

    def terminate(self):
        self._done = True

    def episodeDone(self, stepI):
        return any(
            crit(self, stepI=stepI)
            for crit in self.EPISODE_TERMINATION_CRITERIA)

    def setup(self):
        """
        Setup the environment - this shouldn't be done in the constructor to
        enable override.
        This asusmes the problem uses a gym environment. Override otherwise.
        """
        logger.info("[%s] Problem setup" % self.__class__.__name__)
        if self.GYM_ENVIRONMENT_NAME is None:
            raise NotImplementedError()
        self._env = gym.make(self.GYM_ENVIRONMENT_NAME)
        self.observationSpace = self._env.observation_space
        self.actionSpace = self._env.action_space

    ###
    # Some helper function to retrieve information about the environment.
    # These are pre-implemented for any gym environment, and should
    # be overriden otherwise
    ###

    def getStatesList(self):
        """
        Returns the list of possible states.
        Override this function if you're not defining a gym environment.
        This function should only be called if the problem bears a discrete
        state space.
        """
        if self.env is None:
            raise NotImplementedError()
        if self.DOMAIN['state'] == Spaces.Discrete:
            return range(self.env.action_space.n)
        raise ProblemException("Continuous state space")

    def getStatesDim(self):
        """
        Return the number of dimension of the state space
        """
        if self.env is None:
            raise NotImplementedError()
        return len(self.env.observation_space.low)

    def getStatesBounds(self):
        """
        Returns the max and min values each dimension can take.
        These are returned as two tuples, `low` and `high`, where both
        are a list of as many elements as there is dimension to the state space.
        """
        if self.env is None:
            raise NotImplementedError()
        return (
            self.env.observation_space.low,
            self.env.observation_space.high)

    def getActionsList(self):
        """
        Returns the list of possible actions.
        Override this function if you're not defining a gym environment.
        This function should only be called if the problem bears a discrete
        state space.
        """
        if self.env is None:
            raise NotImplementedError()
        if self.DOMAIN['action'] == Spaces.Discrete:
            return range(self.env.action_space.n)
        raise NotImplementedError()

    # Problem execution methods

    def step(self, action):
        """
        The agent take the given action and receives back the new state,
        the reward, whether the episode is terminated and optionally
        some additional debug information.
        Override this function if you're not defining a gym environment.
        """
        newObservation, reward, self._done, info = self._env.step(action)
        return newObservation, reward, self._done, info

    def reset(self):
        """
        Reset the state of the environment for a new episode.
        Override this function if you're not defining a gym environment.
        """
        self._done = False
        return self._env.reset()

    def render(self, close=False):
        """
        Render the environment (server-side)
        Override this function if you're not defining a gym environment.
        """
        return self._env.render(close=close)

    def release(self):
        """
        Release handles and memory if manual intervention is required.
        """
        pass

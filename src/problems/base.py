# -*- coding: utf8 -*-

from __future__ import unicode_literals

import gym

from parametizable import Parametizable
from consts import ParamsTypes, Spaces


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
            'range': (-1, float('inf'))
        }
    }

    PARAMS_DEFAULT = {
        'maxSteps': 100
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

    def __init__(self, **kwargs):
        super(BaseProblem, self).__init__()
        self._done = False
        self._env = None

    def episodeDone(self, stepI):
        return any(
            crit(self, stepI=stepI)
            for crit in self.EPISODE_TERMINATION_CRITERIA)

    def setup(self):
        """
        Setup the environment - this shouldn't be done in the constructore.
        """
        if self.GYM_ENVIRONMENT_NAME is None:
            raise NotImplementedError()
        self._env = gym.make(self.GYM_ENVIRONMENT_NAME)

    def step(self, action):
        """
        The agent take the given action and receives back the new state,
        the reward, whether the episode is terminated and optionally
        some additional debug information.
        """
        newObservation, reward, self._done, info = self._env.set(action)
        return newObservation, reward, self._done, info

    def reset(self):
        """
        Reset the state of the environment for a new episode.
        """
        return self._env.reset()

    def render(self):
        """
        Render the environment (server-side)
        """
        return self._env.render()

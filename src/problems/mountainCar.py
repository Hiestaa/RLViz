# -*- coding: utf8 -*-

from __future__ import unicode_literals

from problems.base import BaseProblem
from consts import Spaces


class MountainCar(BaseProblem):
    """
    Wraps up Gym's MountainCar-v0 environment
    """
    GYM_ENVIRONMENT_NAME = 'MountainCar-v0'

    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Continuous
    }


class MountainCarCustom(BaseProblem):
    """
    Wraps up Gym's MountainCar-v0 environment
    This additionally setup a strongly negative reward each time the car hits \
the left side of the ramp.
    This will teach it not to use the help that stops \
the car instantly on top left of the hill.
    """
    GYM_ENVIRONMENT_NAME = 'MountainCar-v0'

    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Continuous
    }

    def __init__(self, **kwargs):
        super(MountainCarCustom, self).__init__(**kwargs)

        self._lastObservation = None

    def step(self, action):
        newObservation, reward, self._done, info = self._env.step(action)
        if self._lastObservation is not None:
            # TODO: and lastObservation.position > left limit
            #       and speed > speed limit
            # reward = -self.maxSteps
            pass
        self._lastObservation = newObservation
        return newObservation, reward, self._done, info

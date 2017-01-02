# -*- coding: utf8 -*-

from __future__ import unicode_literals

from problems.base import BaseProblem
from consts import Spaces, ParamsTypes
import utils


class MountainCar(BaseProblem):
    """
    Wraps up Gym's MountainCar-v0 environment
    """
    GYM_ENVIRONMENT_NAME = 'MountainCar-v0'

    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Continuous
    }

    def release(self):
        if self._env.viewer is not None:
            self._env.viewer.close()


class MountainCarCustom(BaseProblem):
    """
    Wraps up Gym's MountainCar-v0 environment
    This adds an additional constraint to the problem: the car recieves a
stronger negative reward when it ramps up the left side of the hill.
    """
    GYM_ENVIRONMENT_NAME = 'MountainCar-v0'

    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Continuous
    }

    PARAMS = utils.extends(BaseProblem.PARAMS, tolerance=ParamsTypes.Number)

    PARAMS_DOMAIN = utils.extends(BaseProblem.PARAMS_DOMAIN, tolerance={
        'range': (0, 100)
    })

    PARAMS_DEFAULT = utils.extends(BaseProblem.PARAMS_DEFAULT, tolerance=10)

    PARAMS_DESCRIPTION = utils.extends(
        BaseProblem.PARAMS_DESCRIPTION,
        tolerance="""
Tolerance for the car to reach the left side - 100% means as soon as the car
start ramping up left if receives a lower negative reward.
""")

    def __init__(self, **kwargs):
        super(MountainCarCustom, self).__init__(**kwargs)

    def step(self, action):
        newObservation, reward, self._done, info = self._env.step(action)
        limit = self._env.observation_space.low[0] * self.tolerance / 100
        if newObservation[0] < limit:
            exceedent = abs(newObservation[0] - limit)
            # reward is a (negative) percentage of how far we went on the left.
            # It is only proportional to the exceedent, which is itself
            # invertly proportional to the tolerance
            # (high tolerance, low exceedent, fair reward)
            # (low tolerance, high exceeded, very low reward)
            reward = exceedent * 100.0 / self._env.observation_space.low[0]
            reward = int(round(reward))
        return newObservation, reward, self._done, info

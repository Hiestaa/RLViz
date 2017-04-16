# -*- coding: utf8 -*-

from __future__ import unicode_literals


import itertools
import math

import numpy as np
from algorithms.policies import Policies
from algorithms.hints import EPSILON_PARAMETER_HELP
from parametizable import Parametizable
from consts import Spaces, ParamsTypes


class Discretizer(object):
    """
    Helper to discretize a bounded coutinuous vector space.

    BEWARE: the precision factor controls the resource usage of this object.
    IT DOES NOT STORE THE ENTIRE DISCRETIZED SPACE
    but it does build it on calling `discretize` (which) returns a generator,
    it's up to you to store the whole beast in memory or not.

    The helper provides to handy methods:
    * `discretize()` will return a list of all possible values the space can
      hold. The values will be linearly distributed over each dimension of the
      space.
    * `trunc(vec:tuple)` truncate the value to the closest smaller value for
      each dimension of the state space
    The following attibute are available
    * low: vector of N dimensions representing the minimum value on each
      dimension
    * high: vector of N dimension representing the maxinum value on each
      dimension
    * steps: the value of the step in each dimension. The list of values for
      a given dimension is given by Un = low + steps * n

    To avoid floating point arithmetic nonsense, the numbers are rounded
    to some number of digits that depends on the precision and the boundaries
    of the space
    """
    def __init__(self, low, high, precision=10):
        """
        Build the discretized on the given N-dimensional space described by the
        given box, at the given precision.
        * low: low value for each dimension of the box
        * high: high value for each dimension of the box
        * precision: precision of the discretized space
        """
        super(Discretizer, self).__init__()
        self.precision = precision

        self.low = low
        self.high = high

        values, self.steps = zip(*[
            np.linspace(
                self.low[dim],
                self.high[dim],
                self.precision,
                retstep=True)
            for dim in xrange(len(self.low))
        ])
        self.low = [round(v, self._getNDigits(dim))
                    for dim, v in enumerate(self.low)]
        self.high = [round(v, self._getNDigits(dim))
                     for dim, v in enumerate(self.high)]
        self.steps = [round(v, self._getNDigits(dim))
                      for dim, v in enumerate(self.steps)]

    def _getNDigits(self, dim):
        return max(
            int(
                round(
                    # log10(0.1) = -1, log10(0.01) = -2, etc...
                    math.log10(
                        abs(self.low[dim] - self.high[dim]))) * -1 +
                    # log10(10) = 1, log10(100) = 2, ...
                    math.log10(self.precision) + 2),
            0)

    def discretize(self):
        """
        Discretize the given continuous space given as a gym `Box` as a list of
        of possible values between the lower and upper bound of the environment.
        """

        values = [
            np.linspace(
                self.low[dim],
                self.high[dim],
                self.precision)
            for dim in xrange(len(self.low))
        ]
        rvalues = [
            [round(self.low[dim] + n * self.steps[dim],
                   self._getNDigits(dim))
             for n, v in enumerate(linspace)]
            for dim, linspace in enumerate(values)]

        # blows up your memory :p
        return itertools.product(*rvalues)

    def _threshold(self, val, dim):
        """
        find the next previous for (=truncate) the given value, for the
        given dimension.
        """
        # round to something sane to avoid floating operation troubles
        val = round(val, self._getNDigits(dim))
        # translation to origin 0
        val = val - self.low[dim]
        # how much steps do we have in vals?
        nb = round(val / self.steps[dim])

        val = nb * self.steps[dim]
        # revert translation
        return round(val + self.low[dim], self._getNDigits(dim))

    def round(self, vector):
        return tuple([
            self._threshold(vector[x], x)
            for x in xrange(len(vector))])


class AlgoException(Exception):
    pass


class BaseAlgo(Parametizable):
    """Common methods for all algorithms. Also defines the set of attributes
    that will need to be populated by the children.
    This class does not contain implementation and should not be instanciated
    directly. Use one of the children instead"""

    """
    Applicable domain of this algorithm.
    All children should override this, if necessary.
    As is, the algorithm will only be applicable to the most simple problems
    that have a discrete action space and a discrete state space.
    """
    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Discrete
    }

    """
    List of parameters this algorithm should expect to be tunable.
    The constructor will take care of declaring the object attribute with the
    proper value, either from constructor parameters or the parameters default
    value below.
    Keys are parameter names and values should be values from the enumberation
    `ParamsTypes`.
    """
    PARAMS = {
        'epsilon': ParamsTypes.Number
    }

    """
    Applicable domain for algorithm parameters. Each domain should be an object
    holding (optionally) the fields:
    * values: a list of values the parameter can accept
    * range: only applicable to number values, the min/max values the parameter
    can take.
    """
    PARAMS_DOMAIN = {
        'epsilon': {
            'values': ('1/k', '1/log(k)', '1/log(log(k))'),
            'range': (0, 1)
        }
    }

    """
    Default values for parmeters. Beware that the domain won't be validated
    here
    """
    PARAMS_DEFAULT = {
        'epsilon': '1/k'
    }

    """
    Hints as to what the parameters do and how they affect learning.
    These will be used (if available) to provide a help tooltip to the user.
    """
    PARAMS_DESCRIPTION = {
        'epsilon': EPSILON_PARAMETER_HELP
    }

    """
    The policy this algorithm should be using. Should be one of the `Policies`
    enumerated values which contain classes and will be instanciated when
    constructing the algorithm given all parameters the algorithm received.
    The algorithm should take care of declaring and validating the parameters
    the policy requires (e.g.: e-greedy)
    """
    POLICY = Policies.EGreedy

    def __init__(self, **kwargs):
        super(BaseAlgo, self).__init__(**kwargs)

        self._policy = self.POLICY(**kwargs)

    def setup(self, problem):
        """
        Some algorithm may require setup - override this function in this case.
        This performs whatever action is necessary to tailor the algorithm to
        a specific problem.
        """
        pass

    def startEpisode(self, initState):
        """
        Called once at the beginning of each episode given the initial state
        for this episode.
        Implementing this function is not required.
        """
        pass

    def train(self, prevState, nextState, action, reward, episodeI, stepI):
        """
        Called once for each step of each episode.
        A working implementation of this function is required when subclassing.
        Any implementation should train the agent based on:
        * prevState: the state the agent were in _before_ taking the action
        * nextState: the next state the agent is in _after_ taking the action
        * action: the action the agent just took
        * reward: the reward associated with this action
        * episodeI: number of episodes run so far
        * stepI: number of steps run so far for the current episode
        The function should return the next action the agent should take
        assuming the agent is currently in state `nextState`.
        Note: minial implementation for this function is to return a random
        sample from the action space.
        """
        raise NotImplementedError()

    def endEpisode(self, totalReturn):
        """
        Called once at the end of each episode, given the total return received
        for this episode (sum of the cummulated rewards)
        """
        pass

    def pickAction(self, state, episodeI, optimize=False):
        """
        Returns the best action to take in the given state according to the
        defined policy.
        The episode number is given for indicative purpose.
        """
        raise NotImplementedError()

    def actionValue(self, state, action):
        """
        Returns a value indicating how good picking the given action in the
        given state is.
        """
        return 0

    def dump(self):
        """
        Dump the algorithm into a data structure that can be later reloaded,
        conservating the same weights and parameters.
        """
        raise NotImplementedError()

    @classmethod
    def load(cls, data):
        """
        Load the weight and parameter of this algorithm.
        """
        raise NotImplementedError()

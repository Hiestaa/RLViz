# -*- coding: utf8 -*-

from __future__ import unicode_literals

import itertools

import numpy as np

from algorithms.base import BaseAlgo, Spaces, ParamsTypes, AlgoException
from algorithms.policies import Policies
from algorithms.hints import (
    ALPHA_PARAMETER_HELP, EPSILON_PARAMETER_HELP, GAMMA_PARAMETER_HELP)


class Sarsa(BaseAlgo):
    """
    One of the most simple approach for reinforcement learning.
    Applies value function learning using TD(0) and e-greedy policy improvement.
    No function approximation technique is implemented.
    """
    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Discrete
    }

    PARAMS = {
        'epsilon': ParamsTypes.Number,
        'alpha': ParamsTypes.Number,
        'gamma': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'epsilon': {
            'values': ('1/k', '1/log(k)', '1/log(log(k))'),
            'range': (0, 1)
        },
        'alpha': {
            'values': (0.1, 0.01, 0.001, 0.0001),
            'range': (0.00001, 1.0)
        },
        'gamma': {
            'values': (0, 0.1, 0.5, 0.9, 1.0),
            'range': (0, 1)
        }
    }

    PARAMS_DEFAULT = {
        'epsilon': '1/k',
        'alpha': 0.001,
        'gamma': 1.0
    }

    PARAMS_DESCRIPTION = {
        'epsilon': EPSILON_PARAMETER_HELP,
        'gamma': GAMMA_PARAMETER_HELP,
        'alpha': ALPHA_PARAMETER_HELP
    }

    POLICY = Policies.EGreedy

    def __init__(self, **kwargs):
        """
        Initialize SARSA, assigning the given hyper parameters.
        This does not setup
        """
        super(Sarsa, self).__init__(**kwargs)
        self._Q = {}
        self._isSetup = False

        self._a = self.alpha
        self._g = self.gamma

    def setup(self, allStates, allActions, **kwargs):
        """
        Sarsa performs in discrete action space and requires the
        action state value function table to be initialized arbitrarily
        for each state and action.
        * allStates should be given as a list of all possible states,
          each state being a tuple floats, all of the same length
        * allActions should be the list of possible actions
        """
        self._Q = {
            state: {action: 0 for action in allActions}
            for state in allStates
        }
        self._isSetup = True

    def _assertSetup(self):
        if not self._isSetup:
            raise AlgoException("Algorithm hasn't been setup yet.")

    def pickAction(self, state, episodeI=None):
        """
        Returns the best action according to (for now) the e-greedy policy
        If episodeI is given, it should be the episode index. Used to
        update epsilon for the e-greedy polic
        """
        self._assertSetup()
        return self._policy.pickAction(self.Q[state], episodeI=episodeI)

    def step(self, oldState, newState, action, reward, episodeI, stepI):
        """
        TD(0) policy improvement
        Returns the next action to take
        """
        self._assertSetup()
        # sample a new action following e-greedy
        newAction = self.pickAction(newState, episodeI=episodeI)
        # print "New action: ", newAction
        self._Q[oldState][action] = self._Q[oldState][action] + self._a *\
            (reward +
             self._g * self._Q[newState][newAction] -
             self._Q[oldState][action])
        return newAction


class RoundingSarsa(object):
    """
    Rouding sarsa discretizes the states space to enable sarsa to perform on
    continuous states space problems.
    This makes no assumption of the relationship there may exist between two
    states prior to visiting these states (i.e.: no function approximation).
    """
    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Continuous
    }

    PARAMS = {
        'epsilon': ParamsTypes.Number,
        'alpha': ParamsTypes.Number,
        'gamma': ParamsTypes.Number,
        'precision': ParamsTypes.Number
    }

    PARAMS_DOMAIN = {
        'epsilon': {
            'values': ('1/k', '1/log(k)', '1/log(log(k))'),
            'range': (0, 1)
        },
        'alpha': {
            'values': (0.1, 0.01, 0.001, 0.0001),
            'range': (0.00001, 1.0)
        },
        'gamma': {
            'values': (0, 0.1, 0.5, 0.9, 1.0),
            'range': (0, 1)
        },
        'precision': {
            'values': (10, 100, 1000),
            'range': (5, 10000)
        }
    }

    PARAMS_DEFAULT = {
        'epsilon': '1/k',
        'alpha': 0.001,
        'gamma': 1.0,
        'precision': 100
    }

    PARAMS_DESCRIPTION = {
        'epsilon': EPSILON_PARAMETER_HELP,
        'gamma': GAMMA_PARAMETER_HELP,
        'alpha': ALPHA_PARAMETER_HELP,
        'precision': """
Precision of the space discretization. This is the number of ticks or buckets
in each dimension of the observations space. Recommanded value is 100, expect
very long training time for values higher than this, especially when the
problem's observation space hold a high number dimensions."""
    }

    POLICY = Policies.EGreedy

    def __init__(self, **kwargs):
        super(RoundingSarsa, self).__init__(**kwargs)
        self._p = self.precision
        self._os = None

    def setup(self, observationSpace, actionSpace, **kwargs):
        """
        `observationSpace` and `actionSpace` here are respectively
        gym's `Box` and `Discrete` instances.
        """
        self._os = observationSpace
        values, self._steps = zip(*[
            np.linspace(
                observationSpace.low[x],
                observationSpace.high[x],
                self._precision,
                retstep=True)
            for x in xrange(len(observationSpace.low))
        ])
        allStates = list(itertools.product(*values))
        allActions = range(actionSpace.n)

        super(RoundingSarsa, self).setup(allStates, allActions)

    def _threshold(self, val, step, dim):
        # warning: this assumes rounding started at 0 which may not be the case
        return round(float(val - self._os.low[dim]) / step) * step + \
            self._os.low[dim]

    def _round(self, observations):
        return tuple([
            self._threshold(observations[x], self._steps[x], x)
            for x in xrange(len(observations))])

    def pickAction(self, state):
        self._assertSetup()
        state = self._round(state)
        return super(RoundingSarsa, self).pickAction(state)

    def step(self, oldState, newState, action, reward, episodeI, stepI):
        # simply calls SARSA's `step` function with rounded state values.
        self._assertSetup()
        return super(RoundingSarsa, self).step(
            self._round(oldState),
            self._round(newState),
            action, reward, episodeI, stepI)

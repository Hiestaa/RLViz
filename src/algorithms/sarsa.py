# -*- coding: utf8 -*-

from __future__ import unicode_literals

import itertools
import math

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

    def pickAction(self, state, episodeI=None, optimize=False):
        """
        Returns the best action according to (for now) the e-greedy policy
        If episodeI is given, it should be the episode index. Used to
        update epsilon for the e-greedy polic
        """
        self._assertSetup()
        return self._policy.pickAction(
            self._Q[state], episodeI=episodeI, optimize=optimize)

    def train(self, oldState, newState, action, reward, episodeI, stepI):
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


class RoundingSarsa(Sarsa):
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
        self._oslow = None
        self._oshigh = None

        self._allActions = []

    def setup(self, observationSpace, actionSpace, **kwargs):
        """
        `observationSpace` and `actionSpace` here are respectively
        gym's `Box` and `Discrete` instances.
        """
        # will be updated with rounded values, but we need those values to
        # round :p
        self._oslow, self._oshigh = observationSpace.low, observationSpace.high
        values, self._steps = zip(*[
            np.linspace(
                observationSpace.low[dim],
                observationSpace.high[dim],
                self.precision,
                retstep=True)
            for dim in xrange(len(observationSpace.low))
        ])
        self._oslow = [round(v, self._getNDigits(dim))
                       for dim, v in enumerate(observationSpace.low)]
        self._oshigh = [round(v, self._getNDigits(dim))
                        for dim, v in enumerate(observationSpace.high)]
        self._steps = [round(v, self._getNDigits(dim))
                       for dim, v in enumerate(self._steps)]
        rvalues = [
            [round(self._oslow[dim] + n * self._steps[dim],
                   self._getNDigits(dim))
             for n, v in enumerate(linspace)]
            for dim, linspace in enumerate(values)]
        allStates = list(itertools.product(*rvalues))
        self._allActions = range(actionSpace.n)

        super(RoundingSarsa, self).setup(allStates, self._allActions)

    def _getNDigits(self, dim):
        return int(
            # log10(0.1) = -1, log10(0.01) = -2, etc...
            round(math.log10(
                abs(self._oslow[dim] - self._oshigh[dim]))) * -1 +
            3)

    def _threshold(self, val, step, dim):
        # round to something sane to avoid floating operation troubles
        val = round(val, self._getNDigits(dim))
        # translation to origin 0
        val = val - self._oslow[dim]
        # how much steps do we have in vals?
        nb = round(val / step)

        val = nb * step
        # revert translation
        return round(val + self._oslow[dim], self._getNDigits(dim))

    def _round(self, observations):
        return tuple([
            self._threshold(observations[x], self._steps[x], x)
            for x in xrange(len(observations))])

    def pickAction(self, state, episodeI=None, optimize=False):
        self._assertSetup()
        rstate = self._round(state)
        try:
            return super(RoundingSarsa, self).pickAction(
                rstate, episodeI=episodeI, optimize=optimize)
        except KeyError:
            if all(o < self._oshigh[dim] and o > self._oslow[dim]
                   for dim, o in enumerate(state)):
                import ipdb; ipdb.set_trace()
                print "Rounding error: ", state, 'to', rstate
            # we're likely out of bounds (it seems to happen)
            # just create a virtual state and pick a random policy
            return self._policy.pickRandom({a: 0 for a in self._allActions})

    def train(self, oldState, newState, action, reward, episodeI, stepI):
        # simply calls SARSA's `step` function with rounded state values.
        self._assertSetup()
        try:
            return super(RoundingSarsa, self).train(
                self._round(oldState),
                self._round(newState),
                action, reward, episodeI, stepI)
        except KeyError:
            if all(o < self._oshigh[dim] and o > self._oslow[dim]
                   for dim, o in enumerate(newState)):
                import ipdb; ipdb.set_trace()
                print "Rounding error: ", newState, 'to', self._round(newState)
            # we're likely out of bounds (it seems to happen)
            # just create a virtual state and pick a random policy
            return self._policy.pickRandom({a: 0 for a in self._allActions})

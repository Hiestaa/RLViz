# -*- coding: utf8 -*-

from __future__ import unicode_literals

import math
import random

import utils


class Base(object):
    """
    Common functions for all policies
    Functions defined here should be overridded by children
    Do not use directly - use one of the children instead.
    """
    def __init__(self, **kwargs):
        super(Base, self).__init__()

    def pickAction(self, actionValues, episodeI=None, optimize=False):
        """
        Pick the best action according to the policy.
        * actionValues: association between actions and action values
          in the current state.
        * episodeI: number of the episode currently running. Useful for
          e.g. the e-greedy policy.
        * optimize: indicate to the policy that we should optimize for best
          behavior **ignoring exploration** - i.e. the agent isn't trying
          to learn anymore and really want to fully trust the policy learnt
          so far.
        """
        raise NotImplementedError()


class Greedy(Base):
    """Implement the greedy policy"""
    def __init__(self, **kwargs):
        super(Greedy, self).__init__()

    def pickMax(self, actionValues):
        best = max(actionValues.values())
        for action in actionValues.keys():
            if actionValues[action] == best:
                return action

    def pickAction(self, actionValues, episodeI=None, optimize=False):
        return self.pickMax(actionValues)


class EGreedy(Greedy):
    """Implement the epsilon-greedy policy"""
    UPDATES = {
        '1/k': lambda k: 1 / (k or 1),
        '1/log(k)': lambda k: 1 / (math.log(k or 1) or 1),
        '1/log(log(k))': lambda k: 1 / (math.log(math.log(k or 1) or 1) or 1)
    }

    def __init__(self, epsilon, **kwargs):
        super(EGreedy, self).__init__()
        self.epsilon = epsilon
        self._e = 1 if epsilon in self.UPDATES else epsilon

    def pickRandom(self, actionValues):
        nbActions = len(actionValues)
        return actionValues.keys()[random.randint(0, nbActions - 1)]

    def updateE(self, episodeI):
        if self.epsilon in self.UPDATES:
            self._e = self.UPDATES[self.epsilon](episodeI)

    def pickAction(self, actionValues, episodeI=None, optimize=False):
        if episodeI is not None:
            self.updateE(episodeI)

        if optimize or random.random() > self._e:
            return self.pickMax(actionValues)
        else:
            return self.pickRandom(actionValues)

Policies = utils.enum(Greedy=Greedy, EGreedy=EGreedy)

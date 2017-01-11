# -*- coding: utf8 -*-

from __future__ import unicode_literals

import logging

import utils
from consts import Spaces, ParamsTypes
from algorithms.base import BaseAlgo, AlgoException, Discretizer
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
            'values': (1.0, 0.1, 0.01, 0.001, 0.0001),
            'range': (0.00001, 1.0)
        },
        'gamma': {
            'values': (0, 0.1, 0.5, 0.9, 1.0),
            'range': (0, 1)
        }
    }

    PARAMS_DEFAULT = {
        'epsilon': '1/k',
        'alpha': 1.0,
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

    def _setup(self, allStates, allActions):
        """
        Actual setup - enable children to reuse
        """
        # action-value function.
        # For each possible state, this gives an indication to the agent of
        # how good each possible action is.
        # Initially set to 0, the value will increase or decrease based on
        # the reward got as the agent is running episodes.
        self._Q = {
            state: {action: 0 for action in allActions}
            for state in allStates
        }
        self._isSetup = True

    def setup(self, problem):
        """
        Sarsa performs in discrete action space and requires the
        action state value function table to be initialized arbitrarily
        for each state and action. It therefore assumes the sate space and
        the action space is continuous
        """
        self._setup(problem.getStatesList(), problem.getActionsList())

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

    def actionValue(self, state, action):
        self._assertSetup()
        state = tuple([int(s) for s in state])
        return self._Q[state][action]

    def train(self, oldState, newState, action, reward, episodeI, stepI):
        """
        TD(0) policy improvement
        Returns the next action to take
        TD(0) heavily relies on bootstrapping, which is the idea of learning
        both from our experiences and from our trust of our own knowledge
        of how good a state is from a given state/action pair onwards.
        This recursivity enables 'goodness' information to 'flow' from the
        state of achivement (where the agent realize a suite of actions were
        good) towards the states of the first steps of the episode.
        """
        self._assertSetup()
        # sample a new action following e-greedy
        newAction = self.pickAction(newState, episodeI=episodeI)
        # updates the action value function.
        # we increase a little bit the value of Q for the old state and action
        # we just took a little bit (=learning rate) ...
        self._Q[oldState][action] = self._Q[oldState][action] + self._a *\
            (reward -  # ... in the direction of the error between the
             # reward we got and what we thought the reward would be
             self._Q[oldState][action] +
             # ... plus a factor of how good we think the next state will be
             # (this is called 'bootstrapping')
             self._g * self._Q[newState][newAction])
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

    PARAMS = utils.extends({}, precision=ParamsTypes.Number, **Sarsa.PARAMS)

    PARAMS_DOMAIN = utils.extends({}, precision={
        'values': (10, 100, 1000),
        'range': (5, 10000)
    }, **Sarsa.PARAMS_DOMAIN)

    PARAMS_DEFAULT = utils.extends({}, precision=100, **Sarsa.PARAMS_DEFAULT)

    PARAMS_DESCRIPTION = utils.extends(
        {}, precision="""
Precision of the space discretization. This is the number of ticks or buckets
in each dimension of the observations space. Recommanded value is 100, expect
very long training time for values higher than this, especially when the
problem's observation space hold a high number dimensions.""",
        **Sarsa.PARAMS_DEFAULT)

    POLICY = Policies.EGreedy

    def __init__(self, **kwargs):
        super(RoundingSarsa, self).__init__(**kwargs)
        self._p = self.precision
        self._oslow = None
        self._oshigh = None

        self._allActions = []

        self._discretizer = None

    def setup(self, problem):
        # expect a continuous state space
        self._discretizer = Discretizer(
            problem.observationSpace,
            self.precision)

        allStates = list(self._discretizer.discretize())

        # expect a discrete action state
        self._allActions = range(problem.actionSpace.n)

        self._setup(allStates, self._allActions)

    def pickAction(self, state, episodeI=None, optimize=False):
        self._assertSetup()
        rstate = self._discretizer.round(state)
        try:
            return super(RoundingSarsa, self).pickAction(
                rstate, episodeI=episodeI, optimize=optimize)
        except KeyError as e:
            logging.exception(e)
            # we're likely out of bounds (it seems to happen)
            # just create a virtual state and pick a random policy
            return self._policy.pickRandom({a: 0 for a in self._allActions})

    def actionValue(self, state, action):
        self._assertSetup()
        rstate = self._discretizer.round(state)
        try:
            return super(RoundingSarsa, self).actionValue(rstate, action)
        except KeyError as e:
            logging.exception(e)
            return 0

    def train(self, oldState, newState, action, reward, episodeI, stepI):
        # simply calls SARSA's `step` function with rounded state values.
        self._assertSetup()
        try:
            return super(RoundingSarsa, self).train(
                self._discretizer.round(oldState),
                self._discretizer.round(newState),
                action, reward, episodeI, stepI)
        except KeyError:
            if all(o < self._oshigh[dim] and o > self._oslow[dim]
                   for dim, o in enumerate(newState)):
                print(
                    "Rounding error: ", newState, 'to',
                    self._discretizer.round(newState))
            # we're likely out of bounds (it seems to happen)
            # just create a virtual state and pick a random policy
            return self._policy.pickRandom({a: 0 for a in self._allActions})

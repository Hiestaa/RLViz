# -*- coding: utf8 -*-

from __future__ import unicode_literals


from algorithms.policies import Policies
from algorithms.hints import EPSILON_PARAMETER_HELP
from parametizable import Parametizable
from consts import Spaces, ParamsTypes


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

    def setup(self, **kwargs):
        """
        Some algorithm may require setup - override this function in this case.
        This performs whatever action is necessary to tailor the algorithm to
        a specific problem.
        Since the prototype of this method is highly dependent on the algorithm
        (some may require the dimensionality of the action/state space, some
        may require an comprehensive list of all states and actions, etc...),
        always expect undefined number of keyword arguments to be passed by
        adding the splat operator `**kwargs`
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

# -*- coding: utf8 -*-

from __future__ import unicode_literals


EPSILON_PARAMETER_HELP = """
Controls the proportion of actions that will be taken
greedily compared to the one taken randomly.
The special values 1/k, 1/log(k) and 1/log(log(k)) enable to
slowly decay the epsilon value over iterations to converge towards
a greedy policy that is not subject to stochastic behavior anymore
"""

ALPHA_PARAMETER_HELP = """
Learning rate of the algorithm. Typically the small the value to more
precise will be the learning, but the longer it takes to stabilize and the
less likely it is to escape from a global optimum.
"""

GAMMA_PARAMETER_HELP = """
Discount factor of the bootstrapping process in the Temporal Difference
(action-)value function learning. The closer this is to 1, the more we 'trust'
the agent own knowledge when computing the action value function
update rule.
"""

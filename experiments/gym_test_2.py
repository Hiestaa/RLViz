#! .env/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

# import time
import random
import itertools
# from collections import defaultdict

import gym
import numpy as np

# implementation of the sarsa algorithm on the mountain car using values
# rounding for value function approximation

# Note: discarded because matplotlib was a bitch.
# def plot(Q):
#     """
#     Plot the mountain car action value function.
#     This only account for the two first dimensions of the state space.
#     This plots in a 2 dimensional space circle for each action that is
#     bigger the higher the action value function is for this action.
#     Assumes all states have the same action set.
#     """
#     x, y = zip(*Q.keys())
#     allXs, allYs, allAreas, allColors = [], [], [], []
#     ACTION_COLORS = [
#         (1, 0, 0),
#         (0, 1, 0),
#         (0, 0, 1)
#     ]
#     areas = defaultdict(dict)
#     SEP = 1
#     for a in Q[(x[0], y[0])]:
#         for xi, yi in zip(x, y):
#             bounds = (min(Q[(xi, yi)].values()),
#                       max(Q[(xi, yi)].values()))
#             areas[(xi, yi)][a] = \
#                 np.pi * SEP * Q[(xi, yi)][a] / (bounds[1] - bounds[0])
#     for xi, yi in zip(x, y):
#         order = sorted(
#             range(Q[(xi, yi)].keys()),
#             key=lambda a: Q[(xi, yi)][a])
#         for a in order:
#             allXs.append(xi)
#             allYs.append(yi)
#             allAreas.append(areas[(xi, yi)][a])
#             allColors.append(tuple(ACTION_COLORS[a]))

#     plt.scatter(allXs, allYs, s=allAreas, c=allColors, alpha=0.5)
#     plt.show()


class Sarsa(object):
    def __init__(self, allStates, allActions):
        """
        Sarsa performs in discrete action space and requires the
        action state value function table to be initialized arbitrarily
        for each state and action.
        * allStates should be given as a list of all possible states,
          each state being a tuple floats, all of the same length
        * allActiosn should be the list of possible actions
        """
        super(Sarsa, self).__init__()
        self._Q = {
            state: {action: 0 for action in allActions}
            for state in allStates
        }

        self._e = 0.2  # epsilon, for the epsilon-greedy policy
        self._a = 1  # alpha, learning reat
        self._g = 0.5  # gamma, discount factor

    def pickAction(self, state, episodeI=None):
        """
        Returns the best action according to (for now) the e-greedy policy
        If episodeI is given, it should be the episode index. Used to
        update epsilon for the e-greedy polic
        """
        def pickMax():
            best = max(self._Q[state].values())
            for action in self._Q[state].keys():
                if self._Q[state][action] == best:
                    return action

        def pickRandom():
            nbActions = len(self._Q[state])
            return self._Q[state].keys()[random.randint(0, nbActions - 1)]

        if episodeI is not None:
            self._e = 1.0 / (episodeI or 1)
            # print "e=", self._e

        if random.random() > self._e:
            return pickMax()
        else:
            return pickRandom()

    def train(self, oldState, newState, action, reward, episodeI):
        """
        TD(0) policy improvement
        Returns the next action to take
        """
        # sample a new action following e-greedy

        # print "train:", oldState, newState, action, reward
        newAction = self.pickAction(newState, episodeI=episodeI)
        # print "New action: ", newAction
        self._Q[oldState][action] = self._Q[oldState][action] + self._a *\
            (reward +
             self._g * self._Q[newState][newAction] -
             self._Q[oldState][action])
        return newAction


class RoundingSarsa(object):
    """
    Rouding sarsa dummily uses sarse on a discretized space
    This makes no assumption of the relationship there may exist between two
    states prior to visit.
    Requires a discrete action space.
    Observation space is assumed to be continuous, a gym Box
    """
    def __init__(self, observationSpace, actionSpace, d=2):
        super(RoundingSarsa, self).__init__()
        self._precision = 100
        self._os = observationSpace
        values, self._steps = zip(*[
            np.linspace(
                observationSpace.low[x],
                observationSpace.high[x],
                self._precision,
                retstep=True)
            for x in xrange(d)
        ])
        allStates = list(itertools.product(*values))
        allActions = range(actionSpace.n)

        self.sarsa = Sarsa(allStates, allActions)

    def _threshold(self, val, step, dim):
        # warning: this assumes rounding started at 0 which may not be the case
        return round(float(val - self._os.low[dim]) / step) * step + \
            self._os.low[dim]

    def _round(self, observations):
        return tuple([
            self._threshold(observations[x], self._steps[x], x)
            for x in xrange(len(observations))])

    def pickAction(self, state):
        state = self._round(state)
        return self.sarsa.pickAction(state)

    def train(self, oldState, newState, action, reward, episodeI):
        return self.sarsa.train(
            self._round(oldState),
            self._round(newState),
            action, reward, episodeI)


RENDER_EPISODES_SKIP = 1000
# load the environment
env = gym.make('MountainCar-v0')
agent = RoundingSarsa(env.observation_space, env.action_space)
for i_episode in range(1, 20001):
    # reset the enviroment at the beginning of each episode
    observation = env.reset()
    # import ipdb; ipdb.set_trace()
    action = agent.pickAction(observation)
    done = False
    episodeReturn = 0
    # up to a 100 steps
    t = 0
    for t in xrange(1000):
        if (i_episode - 1) % RENDER_EPISODES_SKIP == 0:
            env.render()  # render the environment
        # print(observation)
        # take action, get back the reward and the observations
        newObservation, reward, done, info = env.step(action)
        episodeReturn += reward

        action = agent.train(
            observation, newObservation, action, reward, i_episode)

        observation = newObservation

        if done:  # the episode is terminated (we 'lost'/'won')
            break

    # plot(agent.sarsa._Q)

    print("Episode %d finished after %d timesteps" % (i_episode, t + 1))
    print "Episode %d Return: " % i_episode, episodeReturn


while True:
    observation = env.reset()
    agent.pickAction(observation)
    done = False
    while not done:
        env.render()  # render the environment
        observation, reward, done, info = env.step(action)
        action = agent.pickAction(observation)
        if done:
            break


# Using the following line, gym can record the execution of the environment
# env.monitor.start('/tmp/experiment-name-1')

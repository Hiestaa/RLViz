#! .env/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import time
import gym

# default dummy environment execution over 20 episodes

# load the environment
env = gym.make('CartPole-v0')
for i_episode in range(20):
    # reset the enviroment at the beginning of each episode
    observation = env.reset()
    # up to a 100 steps
    for t in range(100):
        env.render()  # render the environment
        print(observation)
        action = env.action_space.sample()  # sample a random action
        # take action, get back the reward and the observations
        observation, reward, done, info = env.step(action)
        if done:  # the episode is terminated (we 'lost'/'won')
            print("Episode finished after {} timesteps".format(t + 1))
            time.sleep(1)
            break


# Using the following line, gym can record the execution of the environment
# env.monitor.start('/tmp/experiment-name-1')

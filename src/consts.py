# -*- coding: utf8 -*-

from __future__ import unicode_literals

import utils

Spaces = utils.enum(Discrete='Discrete', Continuous='Continuous')
ParamsTypes = utils.enum(Number='Number', String='String', Boolean="Boolean")
# Hooks for inspectors. Various hooks will be dispatched at specific moment of
# the lifetime of the agent with different sets of parameters
Hooks = utils.enum(
    # Called after each episode of the training of the agent.
    # It is up to the inspector not to push messages too often, or training may
    # be slowed down by an IO bottleneck.
    # Provided parameters are:
    # * iEpisode: current episode number
    # * nEpisodes: total number of episodes for this session
    # * episodeReturn: the total reward return for this episode,
    # * episodeSteps: number of steps during this episode,
    # * episodeDuration: (time) duration of the episode, in number of seconds.
    #   If the episode is rendered, a number that is consistent with previous
    #   measurements will be returned instead of the real duration to avoid
    #   ridiculous outliners.
    'trainingProgress')

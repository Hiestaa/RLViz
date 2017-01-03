# -*- coding: utf8 -*-

from __future__ import unicode_literals

from inspectors.base import Base
import utils
from consts import ParamsTypes, Hooks


class EfficiencyInspector(Base):
    """
    Efficiency inspector shows the evolution of the reward or the number of
    steps per episode during a full run (both cannot be shown on the same
    graph to prevent cluterring)
    If its 'reset' parameter is False (the default) it will not reset when
    starting a new training, but rather show the new data on the same plot as
    the old one for comparison purposes.
    """
    PARAMS = {
        'frequency': ParamsTypes.Number,
        'metric': ParamsTypes.String,
        'reset': ParamsTypes.Boolean
    }
    PARAMS_DOMAIN = {
        'frequency': {
            'values': [20, 50, 100, 500],
            'range': [10, float('inf')]
        },
        'metric': {
            'values': ['Return', 'Steps', 'Time']
        },
        'reset': {
            # hello captain obvious, this is here for consistency
            'values': [True, False]
        }
    }
    PARAMS_DEFAULT = {
        'frequency': 50,
        'metric': 'Steps',
        'reset': False
    }
    PARAMS_DESCRIPTION = {
        'frequency': "Progress update frequency. This indicates how many ticks\
to expect during the course of the execution.",
        'metric': "The metric to plot - Return shows the return per episode - \
Steps shows the number of steps per episode.",
        'reset': "Set to True to reset to plot before each training."
    }

    HOOK = Hooks.trainingProgress

    def __init__(self, *args, **kwargs):
        super(EfficiencyInspector, self).__init__(*args, **kwargs)

        self._notifyIfNotTooFrequent = utils.makeProgress(
            0, self.frequency, self._notify)

    def _notify(self, pcVal, iEpisode, nEpisodes, episodeReturn,
                episodeSteps, episodeDuration):
        """
        Called to report execution progress.
        * pcVal: percentage of the progression, a float betwen 0 and 100
        * iEpisode: number of the episode currently running (or just terminated)
        * nEpisodes: total number of episodes expected to be run overall
        * episodeReturn: return received for the episode `iEpisode`.
        * episodeSteps: number of steps the episode `iEpisode` took to complete.
        * episodeDuration: time it took to run this episode
        """
        # need to send the uid, as well as some kind of command / reply-to /
        # routing key to the message
        self.send({
            'route': 'inspect',
            'uid': self.uid,
            'iEpisode': iEpisode,
            'nEpisodes': nEpisodes,
            'episodeReturn': episodeReturn,
            'episodeSteps': episodeSteps,
            'episodeDuration': episodeDuration
        })

    def __call__(self, iEpisode, nEpisodes, episodeReturn, episodeSteps,
                 episodeDuration, *args, **kwargs):
        """
        Report execution progress following the defined frequency.
        Depending on the number of episodes. some calls will be ignored
        to follow user-defined frequency.
        """
        self._notifyIfNotTooFrequent(
            iEpisode, nEpisodes, episodeReturn=episodeReturn,
            episodeSteps=episodeSteps, episodeDuration=episodeDuration)

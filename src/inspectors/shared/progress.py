# -*- coding: utf8 -*-

from __future__ import unicode_literals

from inspectors.base import Base
import utils
from consts import ParamsTypes, Hooks


class ProgressInspector(Base):
    """
    Simplest inspector there can be, simply report progression of the
    training process
    """
    PARAMS = {
        'frequency': ParamsTypes.Number
    }
    PARAMS_DOMAIN = {
        'frequency': {
            'values': [100, 1000],
            'range': [10, float('inf')]
        }
    }
    PARAMS_DEFAULT = {
        'frequency': 1000
    }
    PARAMS_DESCRIPTION = {
        'frequency': "Progress update frequency. This indicates how many ticks\
to expect during the course of the execution."
    }

    HOOK = Hooks.trainingProgress

    def __init__(self, *args, **kwargs):
        super(ProgressInspector, self).__init__(*args, **kwargs)

        self._sendProgress = utils.makeProgress(
            0, self.frequency, self._progress)

    def _progress(self, pcVal, iEpisode, nEpisodes, episodeReturn):
        """
        Called to report execution progress.
        * pcVal: percentage of the progression, a float betwen 0 and 100
        * iEpisode: number of the episode currently running (or just terminated)
        * nEpisodes: total number of episodes expected to be run overall
        * episodeReturn: return received for the episode `iEpisode`.
        """
        divisor = self.frequency / 100
        pcVal = float(pcVal) / divisor
        print "Training progress: %.1f%% (episode %d/%d) - return=%d" % (
            pcVal, iEpisode, nEpisodes, episodeReturn)

        # need to send the uid, as well as some kind of command / reply-to /
        # routing key to the message
        self.send({
            'route': 'inspect',
            'uid': self.uid,
            'pcVal': pcVal,
            'iEpisode': iEpisode,
            'nEpisodes': nEpisodes,
            'episodeReturn': episodeReturn
        })

    def __call__(self, iEpisode, nEpisodes, episodeReturn):
        """
        Report execution progress following the defined frequency.
        Depending on the number of episodes. some calls will be ignored
        to follow user-defined frequency.
        """
        self._sendProgress(iEpisode, nEpisodes, episodeReturn=episodeReturn)

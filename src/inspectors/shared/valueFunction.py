# -*- coding: utf8 -*-

from __future__ import unicode_literals

import itertools
import time

import numpy as np

from inspectors.base import Base
import utils
from consts import ParamsTypes, Hooks


def mean(vals):
    return float(sum(vals)) / len(vals)


class ValueFunctionInspector(Base):
    """
    This inspector looks into the action value function and computes the
    (TODO: weighted) average value of each state. More averaging is performed
    if necessary to reduce the value function to a 1 or 2D function that can
    be plotted in a 2D / 3D space.
    """
    PARAMS = {
        'frequency': ParamsTypes.Number,
        'precision': ParamsTypes.Number,
        'shape': ParamsTypes.String,
        'reducer': ParamsTypes.String
    }
    PARAMS_DOMAIN = {
        'frequency': {
            'values': [100, 1000],
            'range': [10, float('inf')]
        },
        'precision': {
            'values': [5, 10, 20, 100],
            'range': [3, 1000]
        },
        'shape': {
            'values': ['2D', '3D']
        },
        'reducer': {
            'values': ['max', 'mean']
        }
    }
    PARAMS_DEFAULT = {
        'frequency': 100,
        'precision': 20,
        'shape': '3D',
        'reducer': 'max'
    }
    PARAMS_DESCRIPTION = {
        'frequency': "Update frequency. This indicates how many updates\
to expect during the course of the execution. Highest values will induce a \
high data transfer rate which may incurr display delays.",
        'precision': "Value function precision. Number of samples used to \
draw the curve. Higher values will have the same effect as a high frequency in \
terms of slow-downs.",
        'shape': "Shape of the curve in terms of dimensions. 2D curve can be \
used to represents variation of value depending on 1 parameter, 3D curve can \
show variation of value based on 2 parameters. Other parameters will be \
available as a slider.",
        'reducer': "Since this shows value-function rather than action-value \
function, we need a way to reduce all action-values to a single values."
    }

    HOOK = Hooks.trainingProgress

    def __init__(self, *args, **kwargs):
        super(ValueFunctionInspector, self).__init__(*args, **kwargs)

        self._lastNotify = time.time()
        self._notifyIfNotTooFrequent = utils.makeProgress(
            0, self.frequency, self._notify)
        self._stepSizes = []

    def setup(self, problem, algo, agent):
        super(ValueFunctionInspector, self).setup(problem, algo, agent)
        self._notify(0, 0, 0)

    def getKeys(self, nbDims):
        if nbDims == 1:
            return ['x']
        if nbDims == 2 and self.shape == '3D':
            return ['x', 'y']
        if nbDims == 2 and self.shape == '2D':
            return ['x', 'param1']
        if nbDims > 2 and self.shape == '3D':
            return ['x', 'y'] + [
                'param%d' % x for x in xrange(1, nbDims - 1)
            ]
        if nbDims > 2 and self.shape == '2D':
            return ['x'] + [
                'param%d' % x for x in xrange(1, nbDims)
            ]

    def _computeValueFunction(self, nbDims, low, high):
        """
        Compute the value-function in `nbDims` dimension where for each
        dimension `x` the lowest value is `low[x]` and the highest value is
        `high[x]`.
        Returns a list of dicts, each dict being one sample from the action
        value function. Each dict will hold the fields:
        * `x`: position on the x axis, this is the dimension 0 of the
          state space
        * [`y`: position on the y axis, only if `shape` is `3D`. This is
           the dimension 1 of the state space, and will shift all dimension
           numbers indicated below by 1 if present]
        * `z`: corresponding value of the action value function for all other
          parameters.
        * `param<I>`: starting at 1, value of the ith dimension of the sample
          of the state space (or (i+1)th dimension if plotting in 3D).
        """

        values, self._stepSizes = zip(*[
            np.linspace(
                low[dim],
                high[dim],
                self.precision,
                retstep=True)
            for dim in xrange(nbDims)])

        allParams = list(itertools.product(*values))
        allActions = self._problem.getActionsList()
        reducer = max if self.reducer == 'max' else mean

        # returns a list
        return [
            utils.extends({
                key: state[k] for k, key in enumerate(self.getKeys(nbDims))
            }, z=reducer([
                self._algo.actionValue(state, action)
                for action in allActions]))
            for state in allParams
        ]

    def _notify(self, pcVal, iEpisode, nEpisodes):
        """
        Notification messages will hold the following fields:
        * route:
        * uid:
        * iEpisode:
        * data:
        * nbDims:
        * low:
        * high:
        * stepSizes:
        * dimensionNames:
        """
        # compute the value function to the given precision.
        if self._problem is None:
            print "WARNING: `%s:%s' Inspector isn't setup." % (
                self.__class__.__name__, str(self.uid))
            data = {}
            nbDims = 0
            low = {}
            high = {}
            stepSizes = {}
            dimensionNames = {}
        else:
            if time.time() - self._lastNotify < max(
                    float(self.precision ** 2 / 5) / 1000.0, 0.1):
                # avoid cluterring the socket
                return

            nbDims = self._problem.getStatesDim()
            low, high = self._problem.getStatesBounds()

            data = self._computeValueFunction(
                nbDims,
                low,
                high)
            low = {
                key: low[k]
                for k, key in enumerate(self.getKeys(nbDims))
            }
            high = {
                key: high[k]
                for k, key in enumerate(self.getKeys(nbDims))
            }
            stepSizes = {
                key: self._stepSizes[k]
                for k, key in enumerate(self.getKeys(nbDims))
            }
            dimensionNames = {
                key: (
                    self._problem.STATE_DIMENSION_NAMES[k]
                    if k < len(self._problem.STATE_DIMENSION_NAMES) else key)
                for k, key in enumerate(self.getKeys(nbDims))
            }
        # need to send the uid, as well as some kind of command / reply-to /
        # routing key to the message
        self.send({
            'route': 'inspect',
            'uid': self.uid,
            'iEpisode': iEpisode,
            'data': data,
            'nbDims': nbDims,
            'low': low,
            'high': high,
            'stepSizes': stepSizes,
            'dimensionNames': dimensionNames
        })

    def __call__(self, iEpisode, nEpisodes, *args, **kwargs):
        """
        Report execution progress following the defined frequency.
        Depending on the number of episodes. some calls will be ignored
        to follow user-defined frequency.
        """
        self._notifyIfNotTooFrequent(iEpisode, nEpisodes)

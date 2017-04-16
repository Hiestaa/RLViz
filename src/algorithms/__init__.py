# -*- coding: utf8 -*-

from __future__ import unicode_literals

import utils
from sarsa import Sarsa, RoundingSarsa
from monteCarlo import MonteCarlo, GlieMonteCarlo

Algorithms = utils.makeMapping(
    [GlieMonteCarlo, MonteCarlo, Sarsa, RoundingSarsa])

# -*- coding: utf8 -*-

from __future__ import unicode_literals

import utils
from sarsa import Sarsa, RoundingSarsa

Algorithms = utils.makeMapping([Sarsa, RoundingSarsa])

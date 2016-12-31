# -*- coding: utf8 -*-

from __future__ import unicode_literals

import utils

Spaces = utils.enum(Discrete='Discrete', Continuous='Continuous')
ParamsTypes = utils.enum(Number='Number', String='String')
Hooks = utils.enum(
    'trainingProgress')

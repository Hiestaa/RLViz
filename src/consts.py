# -*- coding: utf8 -*-

from __future__ import unicode_literals

import utils

Spaces = utils.enum(Discrete='Discrete', Continuous='Continuous')
ParamsTypes = utils.enum(Number='Number', String='String', Boolean="Boolean")
Hooks = utils.enum(
    'trainingProgress')

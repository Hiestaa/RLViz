# -*- coding: utf8 -*-

from __future__ import unicode_literals

from mountainCar import MountainCar, MountainCarCustom
from gridWorld import PresetGridWorld, RandomGridWorld
import utils

Problems = utils.makeMapping([
    MountainCar,
    MountainCarCustom,
    RandomGridWorld,
    PresetGridWorld
])

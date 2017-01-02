# -*- coding: utf8 -*-

from __future__ import unicode_literals

from inspectors.shared.progress import ProgressInspector
from inspectors.shared.valueFunction import ValueFunctionInspector
import utils

Inspectors = utils.makeMapping([ProgressInspector, ValueFunctionInspector])

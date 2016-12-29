# -*- coding: utf8 -*-

from __future__ import unicode_literals


class AgentException(Exception):
        pass


class Agent(object):
    """Run and execute a given algorithm in the given environment."""
    def __init__(self):
        super(Agent, self).__init__()

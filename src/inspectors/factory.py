# -*- coding: utf8 -*-

from __future__ import unicode_literals

from collections import defaultdict
from inspectors import Inspectors


class InspectorsFactory(object):
    """
    Manages the creation and hooking up of inspectors to the agent.
    All inspector creations should be done in the factory.
    All hooks should also go through the factory which will take care
    of calling the inspectors methods.
    """
    def __init__(self, send):
        """
        Initialize the factory.
        The factory requires a `send` parameter which should be a function bound
        to write data to the client. The function should take a dict as argument
        which will be JSON-dumped before being sent to the client.
        """
        super(InspectorsFactory, self).__init__()

        self._inspectors = []
        # event -> callbacks
        self._hookedUp = defaultdict(list)

        self.send = send

    def dispatch(self, hook, *args, **kwargs):
        """
        Dispatch the given parameters to all inspectors bound to the given hook.
        """
        if len(self._hookedUp[hook]) == 0:
            return

        for inspector in self._hookedUp[hook]:
            inspector(*args, **kwargs)

    def registerInspector(self, name, uid, params):
        """
        Register a new inspector subscribed to the given hook.
        The inspector will be called whenever its hook is triggered. Care should
        be taken that the implementation of the inspector matches the expected
        prototype for the declared hook. See inspectors documentation for more
        details as to which inspector should be bound to which hook
        """
        inspector = Inspectors[name](self.send, uid, **params)
        self._hookedUp[inspector.HOOK].append(inspector)

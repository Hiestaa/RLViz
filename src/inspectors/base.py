# -*- coding: utf8 -*-

from __future__ import unicode_literals

from parametizable import Parametizable


class Base(Parametizable):
    """
    Base class for all inspectors.
    Inspectors are functors, meaning they implement the `__call__` function and
    their instances can thus be called directly.
    This fits the vision that inspectors have a sole unique reporting purpose
    and complex system evolution tracking is done through a combination of the
    simple inspectors
    """

    # Declare which hook this inspector should use. The hook defines when
    # the inspector will be called and which parameters will be provided.
    HOOK = None

    def __init__(self, send, uid, **kwargs):
        """
        Initiailize the inspector, provided the `send` function which
        JSON-dumps and write to the client any given data as a dictionnary
        The constructor also expect the `uid` parameter to be provided. This
        should come from the client and should be used to route the messages
        sent by the server to the proper client side widget.
        Additional provided keyword arguments should are expected
        """
        super(Base, self).__init__(**kwargs)

        self._send = send
        self.uid = uid

        self._problem = None
        self._algo = None
        self._agent = None

    def send(self, message):
        # print("[%s:%s] Inspector Notifies" % (
        #     self.__class__.__name__, str(self.uid)))
        self._send(message)

    def setup(self, problem, algo, agent):
        self._problem = problem
        self._algo = algo
        self._agent = agent
        print("[%s:%s] Inspector setup." % (
            self.__class__.__name__, str(self.uid)))

    def __call__(self, *args, **kwargs):
        """
        Call inspector using provided arguments.
        The arguments the functor expects are defined in the `consts.py` file.
        These are specific to the hook the inspector is bound to.
        """
        raise NotImplementedError()

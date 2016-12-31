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

        self.send = send
        self.uid = uid

    def __call__(self, *args, **kwargs):
        """
        Call inspector using provided arguments.
        The arguments the functor expects are defined in the `consts.py` file.
        These are specific to the hook the inspector is bound to.
        """
        raise NotImplementedError()

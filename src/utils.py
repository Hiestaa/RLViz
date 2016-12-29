# -*- coding: utf8 -*-

from __future__ import unicode_literals


def enum(*args, **kwargs):
    """
    Create an enumeration having the given values.

    As the concept of enumeration does not exist in python, this will actually
    create a new type, like a class that is not instanciated (and has no reason
    to be). The class will hold a class attribute for each possible value of
    the enumeration.
    On the top of this, a special, reserved attribute `_fields` will hold the
    set of all possible values for the enumeration (by 'value' we actually mean
    'fields' here, see example below).

    *args -- if the actual value for each enumerated value does not matter, a
             unique integer will be assigned for each one.
    **kwargs -- if the actual value does matter, you can provide it using
                keyword arguments

    Example of use:
    ```
    >>> from tools import utils
    >>> Positivity = utils.enum('positive', 'negative', 'neutral', unknown=-1)
    >>> Positivity._fields
    {'negative', 'neutral', 'positive', 'unknown'}
    >>> Positivity.positive
    0
    >>> Positivity.neutral
    2
    >>> Positivity.unknown
    -1
    ```
    """
    fields = set(args) | set(kwargs.keys())
    enums = dict(zip(args, range(len(args))),
                 _fields=fields, **kwargs)
    return type(str('Enum'), (), enums)

# -*- coding: utf8 -*-

from __future__ import unicode_literals


def makeProgress(minp, maxp, _cb):
    """
    This will create and returns a function to be used to periodically update
    the progression of some computation intensive task..
    The returned function will take a parameter `current` and `maximum`, both
    integers, where `current` is the current state of the progression, and
    `maximum` is the maximum value `current` can have.
    It will call the function given by `_cb` each time the progression
    increased by one unit, giving it this progression value `p` bounded by
    `minp` and `maxp`, the real progression value `current` and `maximum`,
    the maximum value `current` can take.
    This means that the smaller the range between `minp` and `maxp` is,
    the less often `_cb` function will be called.
    This is made to linearly notify the progression of a task only a few times.
    Example of use (may be more understandable):
        >>> def p(v, c, m): print v, c, m
        >>> progress = makeProgress(20, 40, p)
        >>> for i in xrange(1000):
        >>>    progress(i, 1000)
        20 0 1000
        21 50 1000
        22 100 1000
        ...
        39 950 1000
    Note: additional parameters given to the built `progress` function will be
    passed to the given callback `_cb`.
    WARNING: This will not prevent from flooding the console if the same call
    the `progress` is made many times with the same progress value!
    """
    def progress(c, m, *args, **kwargs):
        if m < (maxp - minp) or c % (m / (maxp - minp)) == 0:
            _cb(minp + c * (maxp - minp) / (m or 1), c, m, *args, **kwargs)
    return progress


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


def makeMapping(classes):
    """
    Create a mapping between class name and actual classes.
    """
    return {
        cls.__name__: cls for cls in classes
    }

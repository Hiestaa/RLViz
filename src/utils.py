# -*- coding: utf8 -*-

from __future__ import unicode_literals

import time
import math


def extends(dico, **kwargs):
    """
    Creates a new entry in the given `dico` for each given keyword argument.
    This does NOT override any value if the field does already exist.
    """
    for field, value in kwargs.iteritems():
        if field not in dico:
            dico[field] = value
    return dico


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


def timeFormat(timestamp):
    """
    Format timestamp into the right unit for human readable display.

    timestamp -- either a float (number of seconds) or a datetime object.
    """
    try:
        # timestamp is a datetime?
        timestamp = time.mktime(timestamp.timetuple())
    except:
        pass  # timestamp is already a float
    if timestamp < 10 ** -3:
        return "%.0fus, %0fns" % (timestamp * 10 ** 6,
                                  (timestamp * 10 ** 6 -
                                   int(timestamp * 10 ** 6)) * 1000)
    if timestamp < 1:
        return "%.0fms, %.0fus" % (timestamp * 1000,
                                   (timestamp * 1000 -
                                    int(timestamp * 1000)) * 1000)
    if timestamp < 60:
        return "%.0fs, %.0fms" % (timestamp,
                                  (timestamp - int(timestamp)) * 1000)
    if timestamp < 60 * 60:
        return "%.0fmin, %.0fs" % (math.floor(timestamp / 60), timestamp % 60)
    if timestamp < 60 * 60 * 24:
        return "%.0fh, %.0fmin, %.0fs" \
            % (math.floor(timestamp / (60 * 60)),
               math.floor((timestamp / 60) % 60),
               timestamp % 60)
    else:
        return "%.0fd, %.0fh, %.0fmin, %.0fs" \
            % (math.floor(timestamp / (60 * 60 * 24)),
               math.floor((timestamp / (60 * 60)) % 24),
               math.floor((timestamp / 60) % 60),
               timestamp % 60)

# -*- coding: utf8 -*-

from __future__ import unicode_literals


import utils


ParamsTypes = utils.enum(Number='Number', String='String')


class ParametizableException(Exception):
        pass


class Parametizable(object):
    """
    Parametizable object.
    This automates the process of defining hyper parameters for algorithms that
    user may later be able to tune to create 'instances' of these algorithms.
    The interface defines the list of expected parameters, their types, their
    applicable domain for user-value validation, their default values
    as well as a description for each of them.
    By subclassing this class and overriding this interface, any object can
    define its own set of parameter
    """

    """
    List of parameters this algorithm should expect to be tunable.
    The constructor will take care of declaring the object attribute with the
    proper value, either from constructor parameters or the parameters default
    value below.
    Keys are parameter names and values should be values from the enumberation
    `ParamsTypes`.
    """
    PARAMS = {
    }

    """
    Applicable domain for algorithm parameters. Each domain should be an object
    holding (optionally) the fields:
    * values: a list of values the parameter can accept
    * range: only applicable to number values, the min/max values the parameter
    can take.
    """
    PARAMS_DOMAIN = {
    }

    """
    Default values for parmeters. Beware that the domain won't be validated
    here
    """
    PARAMS_DEFAULT = {
    }

    """
    Hints as to what the parameters do and how they affect learning.
    These will be used (if available) to provide a help tooltip to the user.
    """
    PARAMS_DESCRIPTION = {
    }

    def __init__(self, **kwargs):
        """
        Initialize the object.
        All parameters defined in `self.PARAMS` will check in the keyword
        argument for a user-defined value. If none is found, the default value
        is used.
        All parameters will be defined as a property of the object holding
        either the user-defined value or the default value as a fallback.
        Values given will be validated from the specified domain.
        """
        super(Parametizable, self).__init__()

        for name, val in kwargs.iteritems():
            try:
                if name not in self.PARAMS:
                    raise ParametizableException("Unexpected parameter: %s" % name)

                if name not in self.PARAMS_DOMAIN:
                    raise ParametizableException(
                        "Undeclared domain for parameter: %s" % name)

                domain = self.PARAMS_DOMAIN[name]
                domainValues = domain.get('values', [])
                domainRange = domain.get('range', (0, -1))
                if not (val in domain.get('values', []) or
                        (val >= domainRange[0] and val <= domainRange[1])):
                    raise ParametizableException(
                        "Out-of-domain parameter: %s (%s). Expected one of: %s or "
                        "within range %d, %d." % (name, str(val), str(domainValues),
                                                  domainRange[0], domainRange[1]))
            except:
                print "Error while setting parameter %s to %s." % (
                    name, str(val))
                raise

        for name, typ in self.PARAMS.iteritems():
            setattr(self, name, kwargs.get(name, self.PARAMS_DEFAULT[name]))

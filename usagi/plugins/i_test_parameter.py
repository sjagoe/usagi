# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import abc

from six import add_metaclass

from haas.utils import abstractclassmethod


@add_metaclass(abc.ABCMeta)
class ITestParameter(object):
    """Interface for test parameter plugins.

    A test parameter plugin generates options to pass to
    ``requests.Session.request()``.

    """

    @abstractclassmethod
    def from_dict(cls, data):
        """Create the TestParameter from a dictionary.

        """

    @abc.abstractmethod
    def load(self, config):
        """Context manager to load and return the options to pass to
        ``requests.Session.request()``.

        On context cleanup, this context manager is expected to release
        any resources helf during the HTTP request.

        """

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
class IAssertion(object):

    @abstractclassmethod
    def from_dict(cls, name, var_dict):
        """Create the VarLoader instance from a var name and var value
        dictionary.

        Parameters
        ----------
        name : str
            The name of the var.
        var_dict: dict
            The value of the var before loading.

        """

    @abc.abstractmethod
    def run(self, config, url, case, response):
        """Run the assertion.

        Parameters
        ----------
        config : usagi.config.Config
            The Config that applies to the test case.
        url : str
            The URL that was used for the initial request of this test.
        case : unittest.TestCase
            The `unittest.TestCase`` to be used for reporting errors or
            failures.
        response : requests.Response
            The response from the request being tested.

        """

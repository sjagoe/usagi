# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager

from usagi.utils import ExitStack
from .plugins.test_parameters import HeadersTestParameter


@contextmanager
def ParameterBuilder(config, parameter_loaders):
    """Load all of a test's parameters in a context manager.

    """
    try:
        headers_loader = next(loader for loader in parameter_loaders
                              if isinstance(loader, HeadersTestParameter))
    except StopIteration:
        headers_loader = None
    parameter_loaders = [loader for loader in parameter_loaders
                         if loader is not headers_loader]

    all_headers = {}
    parameters_dict = {  # Parameter defaults
        'method': 'GET',
    }

    with ExitStack() as stack:
        for parameter_loader in parameter_loaders:
            loaded = stack.enter_context(parameter_loader.load(config))
            all_headers.update(loaded.pop('headers', {}))
            parameters_dict.update(loaded)

        if headers_loader is not None:
            headers = stack.enter_context(headers_loader.load(config))
            all_headers.update(headers.get('headers', {}))

        parameters_dict['headers'] = all_headers
        yield parameters_dict

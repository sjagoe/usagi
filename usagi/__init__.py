# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

try:
    from usagi._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = 'notset'

import logging


class NullHandler(logging.Handler):  # pragma: no cover
    def emit(self, record):
        pass


logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

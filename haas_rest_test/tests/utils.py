# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
import os


@contextmanager
def environment(**env):
    old_env = os.environ
    new_env = os.environ.copy()
    new_env.update(env)
    os.environ = new_env
    try:
        yield
    finally:
        os.environ = old_env

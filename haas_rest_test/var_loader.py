# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os

from six import string_types

from .exceptions import InvalidVariable, VariableLoopError


class StringVarLoader(object):

    def __init__(self, name, value):
        super(StringVarLoader, self).__init__()
        self.name = name
        self.value = value

    def load(self, variables):
        return True


class EnvVarLoader(object):

    def __init__(self, name, env_var):
        super(EnvVarLoader, self).__init__()
        self.name = name
        self._env_var = env_var
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        return cls(name=name, env_var=var_dict['env'])

    def load(self, variables):
        if not self._is_loaded:
            try:
                self._value = os.environ[self._env_var]
            except KeyError:
                raise InvalidVariable('FIXME')
            else:
                self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value


class TemplateVarLoader(object):

    def __init__(self, name, template):
        super(TemplateVarLoader, self).__init__()
        self.name = name
        self._template = template
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        return cls(name=name, template=var_dict['template'])

    def load(self, variables):
        if not self._is_loaded:
            try:
                value = self._template.format(**variables)
            except KeyError:
                return False
            try:
                value.format()
            except KeyError:
                # There are still untemplated substitutions
                self._template = value
            else:
                self._value = value
                self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value

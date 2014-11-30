# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os

from jsonschema.exceptions import ValidationError
import jsonschema

from ..exceptions import InvalidVariable, YamlParseError
from .i_var_loader import IVarLoader


class EnvVarLoader(IVarLoader):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Create a var from environment variable',
        'description': 'Var markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'type': {
                'enum': ['env'],
            },
            'env': {
                'type': 'string',
            },
        },
        'required': ['type', 'env']
    }

    def __init__(self, name, env_var, raw):
        super(EnvVarLoader, self).__init__()
        self.name = name
        self._raw = raw
        self._env_var = env_var
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        try:
            jsonschema.validate(var_dict, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(
            name=name,
            env_var=var_dict['env'],
            raw=var_dict,
        )

    def load(self, filename, variables):
        if not self._is_loaded:
            try:
                self._value = os.environ[self._env_var]
            except KeyError:
                raise InvalidVariable(self.name, repr(self._raw))
            else:
                self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value


class TemplateVarLoader(IVarLoader):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Create a var from string template variable',
        'description': 'Var markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'type': {
                'enum': ['template'],
            },
            'template': {
                'type': 'string',
            },
        },
        'required': ['type', 'template']
    }

    def __init__(self, name, template):
        super(TemplateVarLoader, self).__init__()
        self.name = name
        self._template = template
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        try:
            jsonschema.validate(var_dict, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(name=name, template=var_dict['template'])

    def load(self, filename, variables):
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

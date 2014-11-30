# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os

from six import string_types
from jsonschema.exceptions import ValidationError
import jsonschema

from .exceptions import (
    InvalidVariable, InvalidVariableType, VariableLoopError, YamlParseError)


class StringVarLoader(object):

    def __init__(self, name, value):
        super(StringVarLoader, self).__init__()
        self.name = name
        self.value = value

    def load(self, variables):
        return True


class EnvVarLoader(object):

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

    def load(self, variables):
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


class TemplateVarLoader(object):

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


class VarLoader(object):

    def __init__(self, filename):
        super(VarLoader, self).__init__()
        self.filename = filename
        self.loaders = {
            'env': EnvVarLoader,
            'template': TemplateVarLoader,
        }
        self.loader_keys = set(self.loaders.keys())

    def _create_loader(self, name, var):
        if isinstance(var, string_types):
            loader = StringVarLoader(name, var)
        elif isinstance(var, dict):
            try:
                loader_type = var['type']
            except KeyError:
                raise InvalidVariableType(
                    'Missing type for var {0!r}'.format(name))
            if loader_type not in self.loaders:
                raise InvalidVariableType(
                    'Invalid type for var {0!r}: {1!r}'.format(
                        name, loader_type))
            cls = self.loaders[loader_type]
            loader = cls.from_dict(name, var)
        else:
            raise InvalidVariable(name, repr(var))
        return loader

    def _create_loaders(self, var_dict):
        loaders = []
        for name, var in var_dict.items():
            loaders.append(self._create_loader(name, var))
        return loaders

    def load_variable(self, name, var, existing_variables):
        loader = self._create_loader(name, var)
        if not loader.load(existing_variables):
            raise InvalidVariable(name, repr(var))
        return loader.value

    def load_variables(self, var_dict):
        variables = {}
        loaders = self._create_loaders(var_dict)
        while len(loaders) > 0:
            loaded = set(loader for loader in loaders
                         if loader.load(variables))
            if len(loaded) == 0:
                raise VariableLoopError()
            new_vars = ((loader.name, loader.value) for loader in loaded)
            variables.update(new_vars)
            loaders = [loader for loader in loaders if loader not in loaded]
        return variables

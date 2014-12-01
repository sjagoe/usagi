# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import json
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


class FileVarLoader(IVarLoader):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Create a var from the contents of a file',
        'description': 'Var markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'type': {
                'enum': ['file'],
            },
            'file': {
                'type': 'string',
            },
            'format': {
                'enum': ['plain', 'json'],
                'default': 'plain',
                'description': 'Format of the file data',
            },
            'strip': {
                'type': 'boolean',
                'default': True,
                'description': 'False to prevent stripping leading and trailing whitespace from the loaded data.',  # noqa
            },
        },
        'required': ['type', 'file']
    }

    def __init__(self, name, filename, format, strip):
        super(FileVarLoader, self).__init__()
        self.name = name
        self._filename = filename
        self._format = format
        self._strip = strip
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
            filename=var_dict['file'],
            format=var_dict.get('format', 'plain'),
            strip=var_dict.get('strip', True),
        )

    def _get_file_path(self, test_filename):
        if not os.path.isabs(self._filename):
            filename = os.path.join(
                os.path.dirname(os.path.abspath(test_filename)),
                self._filename,
            )
        else:
            filename = self._filename
        return os.path.normcase(os.path.abspath(filename))

    def load(self, filename, variables):
        if not self._is_loaded:
            file_path = self._get_file_path(filename)
            try:
                with open(file_path) as fh:
                    data = fh.read()
            except Exception as exc:
                raise InvalidVariable(
                    'Unable to read file {0!r}: {1!r}'.format(
                        file_path, str(exc)))
            if self._strip:
                data = data.strip()
            format = self._format
            if format == 'plain':
                value = data
            elif format == 'json':
                value = json.loads(data)
            self._value = value
            self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value
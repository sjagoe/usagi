# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
import json

from jsonschema.exceptions import ValidationError
import jsonschema
import yaml

from ..exceptions import YamlParseError
from .i_test_parameter import ITestParameter


class MethodTestParameter(ITestParameter):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'The HTTP method with which to make a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'method': {
                'enum': ['GET', 'POST', 'DELETE', 'PUT', 'HEAD'],
            },
        },
        'required': ['method'],
    }

    def __init__(self, method):
        super(MethodTestParameter, self).__init__()
        self.method = method
        self.name = 'method'

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(method=data['method'])

    @contextmanager
    def load(self, config):
        yield {self.name: self.method}


class HeadersTestParameter(ITestParameter):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'The HTTP headers to add to a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'headers': {
                'type': 'object',
            },
        },
        'required': ['headers'],
    }

    def __init__(self, headers):
        super(HeadersTestParameter, self).__init__()
        self.headers = headers
        self.name = 'headers'

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(headers=data['headers'])

    @contextmanager
    def load(self, config):
        headers = dict(
            (header_name, config.load_variable(header_name, header_value))
            for header_name, header_value in self.headers.items()
        )
        yield {self.name: headers}


class BodyTestParameter(ITestParameter):

    _format_none = 'none'
    _format_plain = 'plain'
    _format_json = 'json'
    _format_yaml = 'yaml'
    _format_multipart = 'multipart'
    _format_handlers = {
        _format_json: json.dumps,
        _format_yaml: lambda d: yaml.safe_dump(
            d, default_flow_style=False)
    }

    _format_content_types = {
        _format_plain: 'text/plain',
        _format_json: 'application/json',
        _format_yaml: 'application/yaml',
    }

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'A body to send with a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'body': {
                'type': 'object',
                'properties': {
                    'format': {
                        'enum': [_format_none, _format_plain, _format_json,
                                 _format_yaml, _format_multipart],
                        'default': _format_none,
                    },
                    'lookup-var': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'False to prevent resolving the value as a var.',  # noqa
                    },
                    'value': {
                        'description': 'The value of the body to send.  This will be encoded according to the format',  # noqa
                        'oneOf': [
                            {'$ref': '#/definitions/str'},
                            {'$ref': '#/definitions/obj'},
                        ],
                    },
                },
                'required': ['value'],
            },
        },
        'required': ['body'],
        'definitions': {
            'str': {
                'type': 'string',
            },
            'obj': {
                'type': 'object',
            },
        },
    }

    def __init__(self, format, lookup_var, value):
        super(BodyTestParameter, self).__init__()
        self._format = format
        self._lookup_var = lookup_var
        self._value = value

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        body = data['body']
        format = body.get('format', cls._format_none)
        value = body['value']

        return cls(
            format=format,
            lookup_var=body.get('lookup-var', True),
            value=value,
        )

    @property
    def _format_handler(self):
        default = lambda d: d
        return self._format_handlers.get(self._format, default)

    @property
    def _content_type(self):
        return self._format_content_types.get(self._format)

    def _get_value(self, config):
        value = self._value
        if self._lookup_var:
            value = config.load_variable('value', value)
        return self._format_handler(value)

    @contextmanager
    def load(self, config):
        result = {}

        content_type = self._content_type
        if content_type is not None:
            headers = result['headers'] = {}
            headers['Content-Type'] = content_type

        result['data'] = self._get_value(config)

        yield result

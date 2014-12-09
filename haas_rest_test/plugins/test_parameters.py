# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

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

    def load(self, config):
        return {self.name: self.method}


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

    def load(self, config):
        headers = dict(
            (header_name, config.load_variable(header_name, header_value))
            for header_name, header_value in self.headers.items()
        )
        return {self.name: headers}


class BodyTestParameter(ITestParameter):

    _format_none = 'none'
    _format_plain = 'plain'
    _format_json = 'json'
    _format_yaml = 'yaml'
    _format_handlers = {
        _format_none: lambda d: d,
        _format_plain: lambda d: d,
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
                'parameters': {
                    'format': {
                        'enum': [_format_none, _format_plain, _format_json,
                                 _format_yaml],
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
        return cls(
            format=body.get('format', cls._format_none),
            lookup_var=body.get('lookup-var', True),
            value=body['value'],
        )

    def load(self, config):
        result = {}
        format = self._format

        header = self._format_content_types.get(format)
        if header is not None:
            headers = result['headers'] = {}
            headers['Content-Type'] = header

        value = self._value
        if self._lookup_var:
            value = config.load_variable('value', value)
        value = self._format_handlers[format](value)

        result['data'] = value

        return result

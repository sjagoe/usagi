# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from jsonschema.exceptions import ValidationError
import jsonschema

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
        'required': ['method']
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
        'required': ['headers']
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

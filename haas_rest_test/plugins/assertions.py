# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import re

from jsonschema.exceptions import ValidationError
import jsonschema

from ..exceptions import YamlParseError


class StatusCodeAssertion(object):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Assertion on status code',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'expected': {
                'type': 'integer',
            },
        },
        'required': ['expected']
    }

    def __init__(self, expected_status):
        super(StatusCodeAssertion, self).__init__()
        self.expected_status = expected_status

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(expected_status=data['expected'])

    def run(self, case, response):
        case.assertEqual(response.status_code, self.expected_status)


class HeaderAssertion(object):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Assertion on an HTTP header',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'header': {
                'type': 'string',
            },
            'value': {
                'type': 'string',
            },
            'regexp': {
                'type': 'string',
            },
        },
        'required': ['header']
    }

    def __init__(self, header, expected_value=None, regexp=False):
        super(HeaderAssertion, self).__init__()
        self.header = header
        self.expected_value = expected_value
        self.regexp = regexp

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        if 'value' in data and 'regexp' in data:
            raise YamlParseError("'value' and 'regexp' are mutually exclusive")
        header = data['header']
        value = None
        regexp = False
        if 'value' in data:
            value = data['value']
        elif 'regexp' in data:
            value = re.compile(data['regexp'])
            regexp = True
        return cls(header, value, regexp)

    def run(self, case, response):
        headers = response.headers
        case.assertIn(self.header, headers)
        header = headers[self.header]
        if self.expected_value is None:
            return
        if self.regexp:
            case.assertRegexpMatches(self.expected_value, header)
        else:
            case.assertEqual(header, self.expected_value)

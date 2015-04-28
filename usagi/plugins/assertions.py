# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import hashlib
import re

from jsonschema.exceptions import ValidationError
import jsonschema
from jq import jq

from ..exceptions import JqCompileError, YamlParseError
from .i_assertion import IAssertion


class StatusCodeAssertion(IAssertion):

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

    def run(self, config, url, case, response):
        msg = '{0!r}: Status {1!r} != {2!r}'.format(
            url, response.status_code, self.expected_status)
        case.assertEqual(response.status_code, self.expected_status, msg=msg)


class HeaderAssertion(IAssertion):

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

    def run(self, config, url, case, response):
        headers = response.headers
        msg = '{0!r}: Header not found: {1!r}'.format(url, self.header)
        case.assertIn(self.header, headers, msg=msg)
        header = headers[self.header]
        if self.expected_value is None:
            return
        if self.regexp:
            msg = '{0!r}: Header {1!r} does not match regexp: {2!r}'.format(
                url, self.header, self.expected_value)
            case.assertRegexpMatches(header, self.expected_value, msg=msg)
        else:
            msg = '{0!r}: Header {1!r} does not match expected: {2!r}'.format(
                url, self.header, self.expected_value)
            case.assertEqual(header, self.expected_value, msg=msg)


class BodyAssertion(IAssertion):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Assertion on body content',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'format': {
                'enum': ['plain', 'json'],
                'default': 'plain',
            },
            'lookup-var': {
                'type': 'boolean',
                'default': True,
                'description': 'False to prevent resolving the value as a var.',  # noqa
            },
            'value': {
                'description': 'The value with which to compare the body',
                'oneOf': [
                    {'$ref': '#/definitions/str'},
                    {'$ref': '#/definitions/obj'},
                ],
            },
            'filter': {
                'description': 'A jq filter to apply to the body and the assertion value before comparison',  # noqa
                'type': 'string',
            },
        },
        'definitions': {
            'str': {'type': 'string'},
            'obj': {'type': 'object'},
        },
        'required': ['value']
    }

    def __init__(self, format, value, jq_filter, lookup_var):
        super(BodyAssertion, self).__init__()
        self.format = format
        self.value = value
        self.jq_filter = jq_filter
        self.lookup_var = lookup_var

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))

        filter_ = data.get('filter', None)
        if filter_ is not None:
            try:
                jq_filter = jq(filter_)
            except ValueError as e:
                raise JqCompileError(str(e))
        else:
            jq_filter = None

        return cls(
            format=data.get('format', 'plain'),
            value=data['value'],
            jq_filter=jq_filter,
            lookup_var=data.get('lookup-var', True),
        )

    def run(self, config, url, case, response):
        value = self.value
        if self.lookup_var:
            value = config.load_variable('value', value)
        if self.format == 'json':
            body = response.json()
        else:
            body = response.text

        jq_filter = self.jq_filter
        if jq_filter is not None:
            value = jq_filter.transform(value)
            body = jq_filter.transform(body)

        msg = '{0!r}: Body does not match expected value'.format(url)
        case.assertEqual(body, value, msg=msg)


class Sha256BodyAssertion(IAssertion):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Assertion the SHA256SUM of the response body',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'expected': {
                'description': 'The hex-encoded SHA256',
                'type': 'string',
            },
        },
        'required': ['expected']
    }

    def __init__(self, expected):
        super(Sha256BodyAssertion, self).__init__()
        self.expected = expected

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))

        return cls(
            expected=data['expected'].lower(),
        )

    def run(self, config, url, case, response):
        expected = self.expected

        sha256sum = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=16834):
            sha256sum.update(chunk)
        sha256 = sha256sum.hexdigest().lower()

        msg = '{0!r}: Body SHA256 does not match expected value'.format(url)
        case.assertEqual(sha256, expected, msg=msg)

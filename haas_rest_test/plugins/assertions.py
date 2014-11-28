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


class StatusCodeAssertion(object):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Assertion on status code ',
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

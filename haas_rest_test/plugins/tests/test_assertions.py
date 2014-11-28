# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import jsonschema

from haas.testing import unittest

from haas_rest_test.exceptions import YamlParseError
from ..assertions import StatusCodeAssertion


class TestStatusCodeAssertion(unittest.TestCase):

    def test_schema(self):
        # Given
        data = {
            'name': 'status_code',
            'expected': 200,
        }

        # When
        assertion = StatusCodeAssertion.from_dict(data)

        # Then
        self.assertIsInstance(assertion, StatusCodeAssertion)

        # Given
        data = {'expected': 200}

        # When
        assertion = StatusCodeAssertion.from_dict(data)

        # Then
        self.assertIsInstance(assertion, StatusCodeAssertion)

        # Given
        data = {
            'name': 'status_code',
            'expected': 200.1,
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            StatusCodeAssertion.from_dict(data)

        # Given
        data = {
            'name': 'status_code',
            'expected': 'string',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            StatusCodeAssertion.from_dict(data)

        # Given
        data = {}

        # When/Then
        with self.assertRaises(YamlParseError):
            StatusCodeAssertion.from_dict(data)

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from six.moves import urllib

from haas.testing import unittest

from ..plugins.assertions import StatusCodeAssertion
from ..config import Config
from ..utils import create_session
from ..web_test import WebTest


class TestWebTest(unittest.TestCase):

    def test_from_dict(self):
        # Given
        config = Config('http', 'test.invalid')
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
        }
        expected_url = urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                config.scheme,
                config.host,
                url,
                None,
                None,
                None,
            ),
        )

        # When
        test = WebTest.from_dict(session, test_spec, config, {})

        # Then
        self.assertIs(test.session, session)
        self.assertIs(test.config, config)
        self.assertEqual(test.name, name)
        self.assertEqual(test.url, expected_url)
        self.assertEqual(test.method, 'GET')
        self.assertEqual(len(test.assertions), 0)

    def test_assertions(self):
        # Given
        config = Config('http', 'test.invalid')
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'assertions': [
                {
                    'name': 'status_code',
                    'expected': 200,
                },
            ],
        }
        assertions = {
            'status_code': StatusCodeAssertion,
        }

        # When
        test = WebTest.from_dict(session, test_spec, config, assertions)

        # Then
        self.assertEqual(len(test.assertions), 1)
        assertion, = test.assertions
        self.assertIsInstance(assertion, StatusCodeAssertion)

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from mock import Mock
import responses
from six.moves import urllib

from haas.testing import unittest

from ..exceptions import InvalidAssertionClass
from ..plugins.assertions import StatusCodeAssertion
from ..config import Config
from ..utils import create_session
from ..web_test import WebTest


class TestWebTest(unittest.TestCase):

    def test_from_dict(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'})
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

    def test_create_with_assertions(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'})
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

    def test_create_invlalid_assertions(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'})
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'assertions': [
                {
                    'name': 'dont_exist',
                },
            ],
        }
        assertions = {
            'status_code': StatusCodeAssertion,
        }

        # When/Then
        with self.assertRaises(InvalidAssertionClass):
            WebTest.from_dict(session, test_spec, config, assertions)

    @responses.activate
    def test_run(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'})
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

        test = WebTest.from_dict(session, test_spec, config, assertions)

        responses.add(
            test.method,
            test.url,
            status=204,
        )

        # When
        case = Mock()
        test.run(case)

        # Then
        case.assertEqual.assert_called_once_with(204, 200)

    # @responses.activate
    def test_connection_error(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'})
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

        test = WebTest.from_dict(session, test_spec, config, assertions)

        # When
        case = Mock()
        case.fail.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            test.run(case)

        # Then
        self.assertTrue(case.fail.called)

    def test_templating_url(self):
        # Given
        config = Config.from_dict({
            'host': 'test.invalid',
            'vars': {'prefix': '/api'},
        })
        session = create_session()
        name = 'A test'
        url = {'template': '{prefix}/test'}
        test_spec = {
            'name': name,
            'url': url,
        }
        expected_url = urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                config.scheme,
                config.host,
                '/api/test',
                None,
                None,
                None,
            ),
        )

        # When
        test = WebTest.from_dict(session, test_spec, config, {})

        # Then
        self.assertEqual(test.url, expected_url)

    def test_invalid_url(self):
        # Given
        config = Config.from_dict({
            'host': 'test.invalid',
            'vars': {'prefix': '/api'},
        })
        session = create_session()
        name = 'A test'
        url = {'something': '{prefix}/test'}
        test_spec = {
            'name': name,
            'url': url,
        }
        test = WebTest.from_dict(session, test_spec, config, {})
        case = Mock()
        case.fail.side_effect = AssertionError

        # When
        with self.assertRaises(AssertionError):
            test.run(case)

        # Then
        self.assertEqual(case.fail.call_count, 1)
        args, kwargs = case.fail.call_args
        self.assertRegexpMatches(
            args[0],
            r"""InvalidVariable\("\{u?'something': u?'\{prefix\}/test'\}",\)"""
        )

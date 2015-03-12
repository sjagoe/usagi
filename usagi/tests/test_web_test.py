# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import itertools
import json

from mock import Mock, patch
import responses
from six.moves import urllib

from haas.testing import unittest

from ..exceptions import InvalidAssertionClass, InvalidParameterClass
from ..plugins.assertions import StatusCodeAssertion
from ..plugins.test_parameters import (
    BodyTestParameter,
    HeadersTestParameter,
    MethodTestParameter,
)
from ..config import Config
from ..utils import create_session
from ..web_test import WebPoll, WebTest


class TestWebTest(unittest.TestCase):

    def setUp(self):
        self.test_parameter_plugins = {
            'body': BodyTestParameter,
            'headers': HeadersTestParameter,
            'method': MethodTestParameter,
        }

    def _get_web_test_method(self, web_test):
        with web_test.test_parameters() as test_parameters:
            return test_parameters['method']

    def test_from_dict(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
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
        test = WebTest.from_dict(
            session, test_spec, config, {}, self.test_parameter_plugins)

        # Then
        self.assertIs(test.session, session)
        self.assertIs(test.config, config)
        self.assertEqual(test.name, name)
        self.assertEqual(test.url, expected_url)
        self.assertEqual(self._get_web_test_method(test), 'GET')
        self.assertEqual(len(test.assertions), 0)

    def test_from_different_method(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'parameters': {'method': 'POST'},
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
        test = WebTest.from_dict(
            session, test_spec, config, {}, self.test_parameter_plugins)

        # Then
        self.assertIs(test.session, session)
        self.assertIs(test.config, config)
        self.assertEqual(test.name, name)
        self.assertEqual(test.url, expected_url)
        self.assertEqual(self._get_web_test_method(test), 'POST')
        self.assertEqual(len(test.assertions), 0)

    def test_create_with_assertions(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
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
        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # Then
        self.assertEqual(len(test.assertions), 1)
        assertion, = test.assertions
        self.assertIsInstance(assertion, StatusCodeAssertion)

    def test_create_invlalid_assertions(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
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
            WebTest.from_dict(
                session, test_spec, config, assertions,
                self.test_parameter_plugins)

    @responses.activate
    def test_run(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
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

        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        responses.add(
            self._get_web_test_method(test),
            test.url,
            status=204,
        )

        # When
        case = Mock()
        test.run(case)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (204, 200))
        self.assertIn('msg', kwargs)

    def test_connection_error(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
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

        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # When
        case = Mock()
        case.fail.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            test.run(case)

        # Then
        self.assertTrue(case.fail.called)

    def test_templating_url(self):
        # Given
        config = Config.from_dict(
            {
                'host': 'test.invalid',
                'vars': {'prefix': '/api'},
            },
            __file__,
        )
        session = create_session()
        name = 'A test'
        url = {
            'type': 'template',
            'template': '{prefix}/test',
        }
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
        test = WebTest.from_dict(
            session, test_spec, config, {}, self.test_parameter_plugins)

        # Then
        self.assertEqual(test.url, expected_url)

    def test_invalid_url(self):
        # Given
        config = Config.from_dict(
            {
                'host': 'test.invalid',
                'vars': {'prefix': '/api'},
            },
            __file__,
        )
        session = create_session()
        name = 'A test'
        url = {'something': '{prefix}/test'}
        test_spec = {
            'name': name,
            'url': url,
        }
        test = WebTest.from_dict(
            session, test_spec, config, {},
            self.test_parameter_plugins)
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
            """InvalidVariableType\(u?['"]Missing type.*"""
        )

    @responses.activate
    def test_create_with_headers(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        header = 'Authorization'
        header_value = 'Basic 1234abc=='
        test_spec = {
            'name': name,
            'url': url,
            'parameters': {
                'headers': {
                    header: header_value,
                },
            },
        }
        assertions = {}

        self.headers = None

        def callback(request):
            self.headers = request.headers
            return (200, {}, '')

        responses.add_callback(
            responses.GET,
            'http://test.invalid/api/test',
            callback=callback,
        )

        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # When
        case = Mock()
        test.run(case)

        # Then
        self.assertIsNotNone(self.headers)
        self.assertIn(header, self.headers)
        self.assertEqual(self.headers[header], header_value)

    def test_create_with_invalid_parameter(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'parameters': {
                'dont_exist': 'value',
            },
        }
        assertions = {}

        # When/Then
        with self.assertRaises(InvalidParameterClass):
            WebTest.from_dict(
                session, test_spec, config, assertions,
                self.test_parameter_plugins)

    @responses.activate
    def test_create_with_body(self):
        # Given
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        expected = {'some': ['json', 'structure']}
        test_spec = {
            'name': name,
            'url': url,
            'parameters': {
                'body': {
                    'format': 'json',
                    'lookup-var': False,
                    'value': expected,
                },
            },
        }
        assertions = {}

        self.body = None
        self.headers = None

        def callback(request):
            self.body = json.loads(request.body)
            self.headers = request.headers
            return (200, {}, '')

        responses.add_callback(
            responses.GET,
            'http://test.invalid/api/test',
            callback=callback,
        )

        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # When
        case = Mock()
        test.run(case)

        # Then
        self.assertIsNotNone(self.body)
        self.assertIsNotNone(self.headers)
        self.assertEqual(self.body, expected)
        self.assertIn('Content-Type', self.headers)
        self.assertEqual(self.headers['Content-Type'], 'application/json')

    @patch('time.sleep')
    @patch('timeit.default_timer')
    @responses.activate
    def test_poll_success(self, default_timer, sleep):
        # Given
        # Disable sleep effect
        sleep.side_effect = lambda t: None

        current_time = itertools.count(0)

        def _default_timer():
            return next(current_time)

        default_timer.side_effect = _default_timer
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'poll': {
                'period': 1,
                'timeout': 5,
            },
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
        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # Then
        self.assertIsInstance(test, WebPoll)

        # Given
        test_count = [0]

        def _test_callback(request):
            current_count = test_count[0]
            test_count[0] = current_count + 1
            if current_count == 4:
                return (200, {}, '')
            return (404, {}, '')

        responses.add_callback(
            self._get_web_test_method(test),
            test.url,
            _test_callback,
        )

        case = Mock()
        case.failureException = self.failureException

        def _assertEqual(value, expected, msg=None):
            if value != expected:
                raise self.failureException(msg)
        case.assertEqual.side_effect = _assertEqual

        # When
        test.run(case)

        # Then
        self.assertEqual(case.assertEqual.call_count, 5)
        calls = case.assertEqual.call_args_list
        call_args = [call[0] for call in calls]
        expected_calls = [
            (404, 200),
            (404, 200),
            (404, 200),
            (404, 200),
            (200, 200),
        ]
        self.assertEqual(call_args, expected_calls)

    @patch('time.sleep')
    @patch('timeit.default_timer')
    @responses.activate
    def test_poll_fail(self, default_timer, sleep):
        # Given
        # Disable sleep effect
        sleep.side_effect = lambda t: None

        current_time = itertools.count(0)

        def _default_timer():
            return next(current_time)

        default_timer.side_effect = _default_timer
        config = Config.from_dict({'host': 'test.invalid'}, __file__)
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
            'poll': {
                'period': 1,
                'timeout': 5,
            },
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
        test = WebTest.from_dict(
            session, test_spec, config, assertions,
            self.test_parameter_plugins)

        # Then
        self.assertIsInstance(test, WebPoll)

        # Given
        test_count = [0]

        def _test_callback(request):
            current_count = test_count[0]
            test_count[0] = current_count + 1
            return (404, {}, '')

        responses.add_callback(
            self._get_web_test_method(test),
            test.url,
            _test_callback,
        )

        case = Mock()
        case.failureException = self.failureException

        def _assertEqual(value, expected, msg=None):
            if value != expected:
                raise self.failureException(msg)
        case.assertEqual.side_effect = _assertEqual

        # When
        with self.assertRaises(self.failureException):
            test.run(case)

        # Then
        self.assertEqual(case.assertEqual.call_count, 5)
        calls = case.assertEqual.call_args_list
        call_args = [call[0] for call in calls]
        expected_calls = [
            (404, 200),
            (404, 200),
            (404, 200),
            (404, 200),
            (404, 200),
        ]
        self.assertEqual(call_args, expected_calls)

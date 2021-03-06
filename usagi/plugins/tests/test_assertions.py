# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import hashlib
import re
import time

from mock import Mock
import requests
import responses

from haas.testing import unittest

from usagi.config import Config
from usagi.exceptions import JqCompileError, YamlParseError
from usagi.tests.common import MockTestCase
from ..assertions import (
    BodyAssertion, HeaderAssertion, Sha256BodyAssertion, StatusCodeAssertion)


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

    def test_failed_assertion(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        response = Mock()
        response.status_code = 400
        case = MockTestCase()
        assertion = StatusCodeAssertion(200)

        # When
        assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (400, 200))
        self.assertIn('msg', kwargs)

    def test_valid_assertion(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        response = Mock()
        response.status_code = 200
        case = MockTestCase()
        assertion = StatusCodeAssertion(200)

        # When
        assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (200, 200))
        self.assertIn('msg', kwargs)


class TestHeaderAssertion(unittest.TestCase):

    def test_no_header(self):
        # Given
        spec = {
            'name': 'header',
        }

        # When
        with self.assertRaises(YamlParseError):
            HeaderAssertion.from_dict(spec)

    def test_conflicting_value_regexp(self):
        # Given
        spec = {
            'name': 'header',
            'header': 'Content-Type',
            'value': 'value',
            'regexp': 'regexp',
        }

        # When
        with self.assertRaises(YamlParseError):
            HeaderAssertion.from_dict(spec)

    def test_no_expected_value(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        response = Mock()
        response.headers = {
            'Content-Type': 'application/json'
        }
        spec = {
            'name': 'header',
            'header': 'Content-Type',
        }

        # When
        assertion = HeaderAssertion.from_dict(spec)

        # Then
        self.assertEqual(assertion.header, spec['header'])
        self.assertEqual(assertion.expected_value, None)
        self.assertEqual(assertion.regexp, False)

        # When
        case = MockTestCase()
        assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertFalse(case.assertRegexpMatches.called)
        self.assertFalse(case.assertEqual.called)

    def test_assert_expected_value(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        content_type = 'application/json'
        expected_content_type = content_type
        response = Mock()
        response.headers = {
            'Content-Type': content_type,
        }
        spec = {
            'name': 'header',
            'header': 'Content-Type',
            'value': expected_content_type,
        }

        # When
        assertion = HeaderAssertion.from_dict(spec)

        # Then
        self.assertEqual(assertion.header, spec['header'])
        self.assertEqual(assertion.expected_value, expected_content_type)
        self.assertEqual(assertion.regexp, False)

        # When
        case = MockTestCase()
        assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (content_type, expected_content_type))
        self.assertIn('msg', kwargs)

        self.assertFalse(case.assertRegexpMatches.called)

    def test_assert_expected_value_failure(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        content_type = 'application/json'
        expected_content_type = 'text/html'
        response = Mock()
        response.headers = {
            'Content-Type': content_type,
        }
        spec = {
            'name': 'header',
            'header': 'Content-Type',
            'value': expected_content_type,
        }

        # When
        assertion = HeaderAssertion.from_dict(spec)

        # Then
        self.assertEqual(assertion.header, spec['header'])
        self.assertEqual(assertion.expected_value, expected_content_type)
        self.assertEqual(assertion.regexp, False)

        # When
        case = MockTestCase()
        case.assertEqual.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (content_type, expected_content_type))
        self.assertIn('msg', kwargs)

        self.assertFalse(case.assertRegexpMatches.called)

    def test_assert_expected_regexp(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        content_type = 'application/github.v3+json'
        expected_content_type = 'application/.*?json'
        response = Mock()
        response.headers = {
            'Content-Type': content_type,
        }
        spec = {
            'name': 'header',
            'header': 'Content-Type',
            'regexp': expected_content_type,
        }

        # When
        assertion = HeaderAssertion.from_dict(spec)

        # Then
        self.assertEqual(assertion.header, spec['header'])
        self.assertEqual(
            assertion.expected_value, re.compile(expected_content_type))
        self.assertEqual(assertion.regexp, True)

        # When
        case = MockTestCase()
        assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertRegexpMatches.call_count, 1)
        call = case.assertRegexpMatches.call_args
        args, kwargs = call
        self.assertEqual(args, (content_type, assertion.expected_value))
        self.assertIn('msg', kwargs)

        self.assertFalse(case.assertEqual.called)

    def test_assert_expected_regexp_failure(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        content_type = 'text/github.v3+json'
        expected_content_type = 'application/.*?json'
        response = Mock()
        response.headers = {
            'Content-Type': content_type,
        }
        spec = {
            'name': 'header',
            'header': 'Content-Type',
            'regexp': expected_content_type,
        }

        # When
        assertion = HeaderAssertion.from_dict(spec)

        # Then
        self.assertEqual(assertion.header, spec['header'])
        self.assertEqual(
            assertion.expected_value, re.compile(expected_content_type))
        self.assertEqual(assertion.regexp, True)

        # When
        case = MockTestCase()
        case.assertRegexpMatches.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            assertion.run(config, 'http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertRegexpMatches.call_count, 1)
        call = case.assertRegexpMatches.call_args
        args, kwargs = call
        self.assertEqual(args, (content_type, assertion.expected_value))
        self.assertIn('msg', kwargs)
        self.assertFalse(case.assertEqual.called)


class TestBodyAssertion(unittest.TestCase):

    def test_missing_value(self):
        # Given
        spec = {
            'type': 'body',
        }
        # When/Then
        with self.assertRaises(YamlParseError):
            BodyAssertion.from_dict(spec)

    def test_body_assertion_plain(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        expected = 'I am a plaintext response'
        spec = {
            'type': 'body',
            'value': expected,
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.text = expected

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['value'], assertion.value))
        self.assertIn('msg', kwargs)

    def test_body_assertion_var(self):
        # Given
        expected = 'Expected var value'
        config = Config.from_dict(
            {'host': 'host', 'vars': {'some_var': expected}},
            __file__,
        )
        spec = {
            'type': 'body',
            'value': {'type': 'ref', 'var': 'some_var'},
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.text = expected

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (expected, expected))
        self.assertIn('msg', kwargs)

    def test_body_assertion_var_failed(self):
        # Given
        response_body = 'Unexpected value'
        expected = 'Expected var value'
        config = Config.from_dict(
            {'host': 'host', 'vars': {'some_var': expected}},
            __file__,
        )
        spec = {
            'type': 'body',
            'value': {'type': 'ref', 'var': 'some_var'},
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.text = response_body

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (response_body, expected))
        self.assertIn('msg', kwargs)

    def test_body_assertion_json(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        expected = {'expected': 'value'}
        spec = {
            'type': 'body',
            'format': 'json',
            'value': expected,
            'lookup-var': False,
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.json.return_value = expected

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['value'], assertion.value))
        self.assertIn('msg', kwargs)

    def test_body_assertion_construct_invalid_jq_filter(self):
        # Given
        spec = {
            'type': 'body',
            'format': 'json',
            'value': '{}',
            'lookup-var': False,
            'filter': 'badjqfilter!'
        }

        # When/Then
        with self.assertRaises(JqCompileError):
            BodyAssertion.from_dict(spec)

    def test_body_assertion_jq_filter(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        value = {
            'object1': {
                'dynamic': 1,
                'static': 'Value1',
            },
            'object2': {
                'dynamic': 2,
                'static': 'Value2',
            },
        }
        expected = value.copy()
        for key, obj in value.items():
            # Deliberately not deterministic
            obj['dynamic'] = obj['dynamic'] + time.time()
        spec = {
            'type': 'body',
            'format': 'json',
            'value': expected,
            'lookup-var': False,
            # Filter to remove the non-deterministic value from
            # response and assertion value
            'filter': 'with_entries(del(.value.dynamic))',
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.json.return_value = value

        expected_call = {
            'object1': {
                'static': 'Value1',
            },
            'object2': {
                'static': 'Value2',
            },
        }

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (expected_call, expected_call))
        self.assertIn('msg', kwargs)

    def test_body_assertion_ineffective_jq_filter(self):
        # Given
        config = Config.from_dict({'host': 'host'}, __file__)
        value = {
            'object1': {
                'dynamic': 1,
                'static': 'Value1',
            },
            'object2': {
                'dynamic': 2,
                'static': 'Value2',
            },
        }
        expected = value.copy()
        for key, obj in value.items():
            # Deliberately not deterministic
            obj['dynamic'] = obj['dynamic'] + time.time()
        spec = {
            'type': 'body',
            'format': 'json',
            'value': expected,
            'lookup-var': False,
            # Filter to remove the non-deterministic value from
            # response and assertion value
            'filter': 'with_entries(del(.value.other))',
        }
        assertion = BodyAssertion.from_dict(spec)
        case = MockTestCase()
        response = Mock()
        response.json.return_value = value

        # When
        assertion.run(config, 'url', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        # The filter has not removed the dynamic value; the original
        # body and assertion value are used for comparison
        self.assertEqual(args, (spec['value'], assertion.value))
        self.assertIn('msg', kwargs)


class TestSha256BodyAssertion(unittest.TestCase):

    def test_missing_value(self):
        # Given
        spec = {
            'type': 'sha256',
        }
        # When/Then
        with self.assertRaises(YamlParseError):
            Sha256BodyAssertion.from_dict(spec)

    @responses.activate
    def test_sha256_assertion_success(self):
        # Given
        url = 'http://localhost'
        body = 'data'.encode('ascii')
        expected = hashlib.sha256(body).hexdigest()
        responses.add(
            responses.GET,
            url,
            body=body,
            status=200,
        )
        response = requests.get(url)

        config = Config.from_dict({'host': 'host'}, __file__)
        spec = {
            'type': 'sha256',
            'expected': expected,
        }
        assertion = Sha256BodyAssertion.from_dict(spec)
        case = MockTestCase()

        # When
        assertion.run(config, url, case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['expected'], assertion.expected))
        self.assertIn('msg', kwargs)

    @responses.activate
    def test_sha256_assertion_failure(self):
        # Given
        url = 'http://localhost'
        expected = hashlib.sha256('data'.encode('ascii')).hexdigest()
        body = 'other-data'.encode('ascii')
        actual = hashlib.sha256(body).hexdigest()
        responses.add(
            responses.GET,
            url,
            body=body,
            status=200,
        )
        response = requests.get(url)

        config = Config.from_dict({'host': 'host'}, __file__)
        spec = {
            'type': 'sha256',
            'expected': expected,
        }
        assertion = Sha256BodyAssertion.from_dict(spec)
        case = MockTestCase()

        # When
        assertion.run(config, url, case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (actual, expected))
        self.assertIn('msg', kwargs)

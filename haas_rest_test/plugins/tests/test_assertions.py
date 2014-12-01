# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import re

from mock import Mock

from haas.testing import unittest

from haas_rest_test.exceptions import YamlParseError
from ..assertions import HeaderAssertion, StatusCodeAssertion


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
        response = Mock()
        response.status_code = 400
        case = Mock()
        assertion = StatusCodeAssertion(200)

        # When
        assertion.run('http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertEqual.call_count, 1)
        call = case.assertEqual.call_args
        args, kwargs = call
        self.assertEqual(args, (400, 200))
        self.assertIn('msg', kwargs)

    def test_valid_assertion(self):
        # Given
        response = Mock()
        response.status_code = 200
        case = Mock()
        assertion = StatusCodeAssertion(200)

        # When
        assertion.run('http://host/uri', case, response)

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
        case = Mock()
        assertion.run('http://host/uri', case, response)

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
        case = Mock()
        assertion.run('http://host/uri', case, response)

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
        case = Mock()
        case.assertEqual.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            assertion.run('http://host/uri', case, response)

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
        case = Mock()
        assertion.run('http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertRegexpMatches.call_count, 1)
        call = case.assertRegexpMatches.call_args
        args, kwargs = call
        self.assertEqual(args, (assertion.expected_value, content_type))
        self.assertIn('msg', kwargs)

        self.assertFalse(case.assertEqual.called)

    def test_assert_expected_regexp_failure(self):
        # Given
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
        case = Mock()
        case.assertRegexpMatches.side_effect = AssertionError
        with self.assertRaises(AssertionError):
            assertion.run('http://host/uri', case, response)

        # Then
        self.assertEqual(case.assertIn.call_count, 1)
        call = case.assertIn.call_args
        args, kwargs = call
        self.assertEqual(args, (spec['header'], response.headers))
        self.assertIn('msg', kwargs)

        self.assertEqual(case.assertRegexpMatches.call_count, 1)
        call = case.assertRegexpMatches.call_args
        args, kwargs = call
        self.assertEqual(args, (assertion.expected_value, content_type))
        self.assertIn('msg', kwargs)
        self.assertFalse(case.assertEqual.called)

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import textwrap

import responses
import yaml

from haas.loader import Loader
from haas.module_import_error import ModuleImportError
from haas.result import ResultCollecter
from haas.suite import find_test_cases, TestSuite
from haas.testing import unittest

from ..exceptions import YamlParseError
from ..yaml_test_loader import YamlTestLoader


class TestYamlTestLoader(unittest.TestCase):

    def setUp(self):
        self.loader = YamlTestLoader(Loader())

    def test_plugins_loaded(self):
        self.assertIn('status_code', self.loader._assertions_map)

    def test_load_yaml_tests(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"

            - name: "A case"
              tests:
                - name: "Download authorization failure"
                  url:
                    template: "{data}/test"
                - name: "Upload authorization failure"
                  url:
                    template: "/foo/{upload}/test"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 3)
        for case in find_test_cases(suite):
            self.assertIsInstance(case, unittest.TestCase)

    @responses.activate
    def test_execute_single_case(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"
                  assertions:
                    - name: status_code
                      expected: 200

        """)

        responses.add(
            responses.GET,
            'http://test.domain/',
            status=200,
        )

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        case = next(find_test_cases(suite))

        # Given
        result = ResultCollecter()

        # When
        case(result)

        # Then
        self.assertTrue(result.wasSuccessful())

    @responses.activate
    def test_execute_single_case_failure(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"
                  assertions:
                    - name: status_code
                      expected: 200

        """)

        responses.add(
            responses.GET,
            'http://test.domain/',
            status=400,
        )

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        case = next(find_test_cases(suite))

        # Given
        result = ResultCollecter()

        # When
        case(result)

        # Then
        self.assertFalse(result.wasSuccessful())

    def test_load_invalid_yaml_tests(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          tests:
            - name: "Test root URL"
              url: "/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        case = next(find_test_cases(suite))
        self.assertIsInstance(case, unittest.TestCase)
        self.assertIsInstance(case, ModuleImportError)

        # Given
        result = ResultCollecter()

        # When/Then
        meth = getattr(case, case._testMethodName)
        with self.assertRaises(YamlParseError):
            meth()

        # When
        case(result)

        # Then
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.errors), 1)

    def test_case_dunder_str(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        case = next(find_test_cases(suite))

        # When
        case_str = str(case)
        description = case.shortDescription()

        # Then
        self.assertEqual(case_str, "'Basic:Test root URL' (/path/to/foo.yaml)")
        self.assertIsNone(description)

    @responses.activate
    def test_case_setup(self):
        # Given
        test_yaml = textwrap.dedent("""
          version: '1.0'

          config:
            host: test.domain

          test-pre-definitions:
            some_tests:
              - name: "Root"
                url: "/"
            more_tests:
              - name: "Post-1"
                url: "/one"
              - name: "Post-2"
                url: "/two"

          cases:
            - name: "Basic"
              case-setup:
                - some_tests
              case-teardown:
                - more_tests
              tests:
                - name: "Another URL"
                  url: "/another"

        """)

        responses.add(
            responses.GET,
            'http://test.domain/',
            status=200,
        )
        responses.add(
            responses.GET,
            'http://test.domain/another',
            status=201,
        )
        responses.add(
            responses.GET,
            'http://test.domain/one',
            status=202,
        )
        responses.add(
            responses.GET,
            'http://test.domain/two',
            status=203,
        )

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 4)

        # When
        result = ResultCollecter()
        suite(result)

        # Then
        self.assertEqual(len(responses.calls), 4)
        self.assertTrue(result.wasSuccessful())

        pre, test, post_1, post_2 = responses.calls

        self.assertEqual(pre.request.url, 'http://test.domain/')
        self.assertEqual(test.request.url, 'http://test.domain/another')
        self.assertEqual(post_1.request.url, 'http://test.domain/one')
        self.assertEqual(post_2.request.url, 'http://test.domain/two')

    def test_load_yaml_tests_case_max_diff_null(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              max-diff: null
              tests:
                - name: "Test root URL"
                  url: "/"
                - name: "Test sub URL"
                  url: "/sub/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 2)
        cls1, cls2 = [type(case) for case in find_test_cases(suite)]
        self.assertIs(cls1, cls2)
        self.assertIsNone(cls1.maxDiff)

    def test_load_yaml_tests_case_max_diff_number(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              max-diff: 1234
              tests:
                - name: "Test root URL"
                  url: "/"
                - name: "Test sub URL"
                  url: "/sub/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When
        suite = self.loader.load_tests_from_yaml(
            test_data, '/path/to/foo.yaml')

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 2)
        cls1, cls2 = [type(case) for case in find_test_cases(suite)]
        self.assertIs(cls1, cls2)
        self.assertEqual(cls1.maxDiff, 1234)

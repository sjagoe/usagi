# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import textwrap

import responses
import yaml

from haas.discoverer import find_test_cases
from haas.loader import Loader
from haas.module_import_error import ModuleImportError
from haas.result import ResultCollecter
from haas.suite import TestSuite
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

            - name: "A group"
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
        self.assertEqual(case_str, 'Basic (/path/to/foo.yaml)')
        self.assertEqual(description, 'Test root URL')

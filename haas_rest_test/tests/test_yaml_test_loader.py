# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import textwrap

from jsonschema.exceptions import ValidationError
import jsonschema
import yaml

from haas.discoverer import find_test_cases
from haas.loader import Loader
from haas.result import ResultCollecter
from haas.suite import TestSuite
from haas.testing import unittest

from ..schema import SCHEMA
from ..yaml_test_loader import YamlTestLoader


class TestSchema(unittest.TestCase):

    def test_schema(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            variables:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          groups:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"
                  expected_status: [200]

            - name: "A group"
              tests:
                - name: "Download authorization failure"
                  url:
                    template: "{data}/test"
                  expected_status: [404]
                - name: "Upload authorization failure"
                  url:
                    template: "/foo/{upload}/test"
                  expected_status: [404]

        """)

        test_data = yaml.safe_load(test_yaml)

        # Validation succeeds
        jsonschema.validate(test_data, SCHEMA)

    def test_schema_no_groups(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            variables:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_top_level_tests(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            variables:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          tests:
            - name: "Download authorization failure"
              url:
                template: "{data}/test"
              expected_status: [404]
            - name: "Upload authorization failure"
              url:
                template: "/foo/{upload}/test"
              expected_status: [404]

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_top_level_single_test(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            variables:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          name: "Download authorization failure"
          url:
            template: "{data}/test"
          expected_status: [404]

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)


class TestYamlTestLoader(unittest.TestCase):

    def setUp(self):
        self.loader = YamlTestLoader(Loader())

    def test_load_yaml_tests(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          groups:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"
                  expected_status: [200]

            - name: "A group"
              tests:
                - name: "Download authorization failure"
                  url:
                    template: "{data}/test"
                  expected_status: [404]
                - name: "Upload authorization failure"
                  url:
                    template: "/foo/{upload}/test"
                  expected_status: [404]

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

    def test_execute_single_case(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          groups:
            - name: "Basic"
              tests:
                - name: "Test root URL"
                  url: "/"
                  expected_status: [200]

        """)

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
        case(result)
        self.assertFalse(result.wasSuccessful())

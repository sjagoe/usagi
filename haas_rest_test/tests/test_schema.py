# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import textwrap

from jsonschema.exceptions import ValidationError
import jsonschema
import yaml

from haas.testing import unittest

from ..schema import SCHEMA


class TestSchema(unittest.TestCase):

    def test_schema(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain
            vars:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

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

        # Validation succeeds
        jsonschema.validate(test_data, SCHEMA)

    def test_schema_no_cases(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain
            vars:
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
            host: test.domain
            vars:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          tests:
            - name: "Download authorization failure"
              url:
                template: "{data}/test"
            - name: "Upload authorization failure"
              url:
                template: "/foo/{upload}/test"

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
            host: test.domain
            vars:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          name: "Download authorization failure"
          url:
            template: "{data}/test"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_missing_host(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            vars:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          cases:
            - name: "Basic"
              tests:
                - name: "Test"
                  url: "/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_bad_host(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: true
            vars:
              api: "/api/v0/json"
              data: "/api/v0/json/data"
              upload: "/api/v0/json/upload"

          cases:
            - name: "Basic"
              tests:
                - name: "Test"
                  url: "/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_missing_config(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          cases:
            - name: "Basic"
              tests:
                - name: "Test"
                  url: "/"

        """)

        test_data = yaml.safe_load(test_yaml)

        # When/Then
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_assertions(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Default method"
                  url: "/"
                  assertions:
                    - name: status_code
                      expected: 200

        """)

        test_data = yaml.safe_load(test_yaml)

        # Validation succeeds
        jsonschema.validate(test_data, SCHEMA)

    def test_schema_invalid_assertions(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Default method"
                  url: "/"
                  assertions:
                    name: status_code
                    expected: 200

        """)

        test_data = yaml.safe_load(test_yaml)

        # Validation succeeds
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_empty_assertions(self):
        # Given
        test_yaml = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "Basic"
              tests:
                - name: "Default method"
                  url: "/"
                  assertions: []

        """)

        test_data = yaml.safe_load(test_yaml)

        # Validation fails
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

    def test_schema_pre_definitions_case_setup(self):
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

        test_data = yaml.safe_load(test_yaml)

        # Validation succeeds
        jsonschema.validate(test_data, SCHEMA)

    def test_schema_bad_pre_definition(self):
        # Given
        test_yaml = textwrap.dedent("""
          version: '1.0'

          config:
            host: test.domain

          test-pre-definitions:
            - name: "Root"
              url: "/"

          cases:
            - name: "Basic"
              tests:
                - name: "Another URL"
                  url: "/another"

        """)

        test_data = yaml.safe_load(test_yaml)

        # Validation fails
        with self.assertRaises(ValidationError):
            jsonschema.validate(test_data, SCHEMA)

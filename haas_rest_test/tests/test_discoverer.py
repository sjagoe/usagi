# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
import textwrap

from haas.discoverer import find_test_cases
from haas.loader import Loader
from haas.suite import TestSuite
from haas.testing import unittest

from ..discoverer import RestTestDiscoverer


class TestDiscoverer(unittest.TestCase):

    def setUp(self):
        self.discoverer = RestTestDiscoverer(Loader())
        self.temp_dir = tempfile.mkdtemp(
            prefix='haas-rest-test-', suffix='.tmp')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_discover_from_file(self):
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
        with tempfile.NamedTemporaryFile(
                delete=False, suffix='.yml', dir=self.temp_dir) as fh:
            fh.write(test_yaml.encode('utf-8'))
        test_filename = fh.name

        # When
        suite = self.discoverer.discover(test_filename)

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 3)
        for case in find_test_cases(suite):
            self.assertIsInstance(case, unittest.TestCase)

    def test_discover_from_directory(self):
        # Given
        test_yaml_1 = textwrap.dedent("""
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
        test_yaml_2 = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "A group"
              tests:
                - name: "Download authorization failure"
                  url:
                    template: "{data}/test"
                - name: "Upload authorization failure"
                  url:
                    template: "/foo/{upload}/test"

        """)
        with tempfile.NamedTemporaryFile(
                delete=False, suffix='.yml', dir=self.temp_dir) as fh:
            fh.write(test_yaml_1.encode('utf-8'))
        with tempfile.NamedTemporaryFile(
                delete=False, suffix='.yml', dir=self.temp_dir) as fh:
            fh.write(test_yaml_2.encode('utf-8'))

        # When
        suite = self.discoverer.discover(self.temp_dir)

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 3)
        for case in find_test_cases(suite):
            self.assertIsInstance(case, unittest.TestCase)

    def test_discover_skip_badly_named_files(self):
        # Given
        test_yaml_1 = textwrap.dedent("""
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
        test_yaml_2 = textwrap.dedent("""
        ---
          version: '1.0'

          config:
            host: test.domain

          cases:
            - name: "A group"
              tests:
                - name: "Download authorization failure"
                  url:
                    template: "{data}/test"
                - name: "Upload authorization failure"
                  url:
                    template: "/foo/{upload}/test"

        """)
        with tempfile.NamedTemporaryFile(
                delete=False, suffix='.ymll', dir=self.temp_dir) as fh:
            fh.write(test_yaml_1.encode('utf-8'))
        with tempfile.NamedTemporaryFile(
                delete=False, suffix='.yml', dir=self.temp_dir) as fh:
            fh.write(test_yaml_2.encode('utf-8'))

        # When
        suite = self.discoverer.discover(self.temp_dir)

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 2)

    def test_discover_no_such_file(self):
        # Given
        test_filename = os.path.join(self.temp_dir, 'dont_exist.yml')

        # When
        suite = self.discoverer.discover(test_filename)

        # Then
        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.countTestCases(), 0)
        for case in find_test_cases(suite):
            self.assertIsInstance(case, unittest.TestCase)

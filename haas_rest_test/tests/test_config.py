# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
import os

from haas.testing import unittest

from ..config import _template_variables


class TestTemplateVariables(unittest.TestCase):

    @contextmanager
    def environment(self, **env):
        old_env = os.environ
        new_env = os.environ.copy()
        new_env.update(env)
        os.environ = new_env
        try:
            yield
        finally:
            os.environ = old_env

    def test_simple(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'template': '{var1}/another/path'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/some/path/another/path',
        }

        # When
        templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_env(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'env': 'ENV_VAR'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/another/path',
        }

        # When
        with self.environment(ENV_VAR='/another/path'):
            templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_env_in_template(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'env': 'ENV_VAR'},
            'var3': {'template': '{var2}/yet/another/path'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/another/path',
            'var3': '/another/path/yet/another/path'
        }

        # When
        with self.environment(ENV_VAR='/another/path'):
            templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_multiple_levels(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'template': '{var1}/another/path'},
            'var3': {'template': '{var2}/yet/another/path'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/some/path/another/path',
            'var3': '/some/path/another/path/yet/another/path'
        }

        # When
        templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_multiple_levels_ordering(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'template': '{var1}/yet/another/path'},
            'var3': {'template': '{var2}/another/path'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/some/path/yet/another/path',
            'var3': '/some/path/yet/another/path/another/path',
        }

        # When
        templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_multiple_levels_ordering_2(self):
        # Given
        variables = {
            'var1': {'template': '{var2}/yet/another/path'},
            'var2': '/some/path',
            'var3': {'template': '{var1}/another/path'},
        }
        expected = {
            'var1': '/some/path/yet/another/path',
            'var2': '/some/path',
            'var3': '/some/path/yet/another/path/another/path',
        }

        # When
        templated_vars = _template_variables(variables)

        self.assertEqual(templated_vars, expected)

    def test_mutual_templating(self):
        # Given
        variables = {
            'var1': {'template': '{var2}/another/path'},
            'var2': {'template': '{var1}/yet/another/path'},
        }

        # When
        with self.assertRaises(RuntimeError):
            _template_variables(variables)

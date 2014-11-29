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

from ..config import _template_variables, Config
from ..exceptions import InvalidVariable, VariableLoopError


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
        templated_vars = _template_variables(variables, __file__)

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
            templated_vars = _template_variables(variables, __file__)

        self.assertEqual(templated_vars, expected)

    def test_var_from_file(self):
        # Given
        variables = {
            'var1': {'file': 'test_data.txt'},
            'var2': {'file': 'test_data.json', 'format': 'json'},
        }
        expected = {
            'var1': 'Test plain text!\n',
            'var2': {'test': 'json'},
        }

        # When
        templated_vars = _template_variables(variables, __file__)

        self.assertEqual(templated_vars, expected)

    def test_var_invalid_file_format(self):
        # Given
        variables = {
            'var1': {'file': 'test_data.txt', 'format': 'unknown'},
        }

        # When
        with self.assertRaises(InvalidVariable):
            _template_variables(variables, __file__)

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
            'var3': '/another/path/yet/another/path',
        }

        # When
        with self.environment(ENV_VAR='/another/path'):
            templated_vars = _template_variables(variables, __file__)

        self.assertEqual(templated_vars, expected)

    def test_multiple_levels(self):
        # Given
        variables = {
            'var1': '/some/path',
            'var2': {'template': '{var4}/another/path'},
            'var3': {'template': '{var2}/yet/another/path'},
            'var4': {'template': '{var1}/again'},
        }
        expected = {
            'var1': '/some/path',
            'var2': '/some/path/again/another/path',
            'var3': '/some/path/again/another/path/yet/another/path',
            'var4': '/some/path/again',
        }

        # When
        templated_vars = _template_variables(variables, __file__)

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
        templated_vars = _template_variables(variables, __file__)

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
        templated_vars = _template_variables(variables, __file__)

        self.assertEqual(templated_vars, expected)

    def test_mutual_templating(self):
        # Given
        variables = {
            'var1': {'template': '{var2}/another/path'},
            'var2': {'template': '{var1}/yet/another/path'},
        }

        # When
        with self.assertRaises(VariableLoopError):
            _template_variables(variables, __file__)

    def test_invalid_type(self):
        # Given
        variables = {
            'var1': {'bad_type': '{var2}/another/path'},
        }

        # When
        with self.assertRaises(InvalidVariable):
            _template_variables(variables, __file__)

    def test_host_from_env_var(self):
        # Given
        config_dict = {
            'host': {'env': 'ENV_VAR'},
        }
        expected = 'host.domain'

        # When
        with self.environment(ENV_VAR=expected):
            config = Config.from_dict(config_dict, __file__)

        # Then
        self.assertEqual(config.host, expected)

    def test_host_from_template(self):
        # Given
        config_dict = {
            'host': {'template': '{var1}.domain'},
            'vars': {'var1': 'host'},
        }
        expected = 'host.domain'

        # When
        config = Config.from_dict(config_dict, __file__)

        # Then
        self.assertEqual(config.host, expected)

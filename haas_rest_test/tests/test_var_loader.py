# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from haas.testing import unittest

from .utils import environment
from ..exceptions import (
    InvalidVariable, InvalidVariableType, VariableLoopError, YamlParseError)
from ..var_loader import (
    StringVarLoader, EnvVarLoader, TemplateVarLoader, VarLoader)


class TestStringVarLoader(unittest.TestCase):

    def test_string_loader(self):
        # Given
        loader = StringVarLoader('name', 'value')

        # Then
        self.assertTrue(loader.load(None))
        self.assertEqual(loader.name, 'name')
        self.assertEqual(loader.value, 'value')


class TestEnvVarLoader(unittest.TestCase):

    def test_validation_failure(self):
        name = 'env_var'
        var_dict = {
            'type': 'foo',
            'env': 'VAR',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            EnvVarLoader.from_dict(name, var_dict)

        name = 'env_var'
        var_dict = {
            'type': 'env',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            EnvVarLoader.from_dict(name, var_dict)

        # Given
        var_dict = {
            'env': 'VAR',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            EnvVarLoader.from_dict(name, var_dict)

    def test_env_var_loader_basic(self):
        # Given
        name = 'env_var'
        var_dict = {
            'type': 'env',
            'env': 'ENV_VAR',
        }
        value = 'Env var value'
        loader = EnvVarLoader.from_dict(name, var_dict)

        # When
        with environment(ENV_VAR=value):
            is_loaded = loader.load(None)

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)

    def test_env_var_loader_no_var(self):
        # Given
        name = 'env_var'
        var_dict = {
            'type': 'env',
            'env': 'ENV_VAR',
        }
        loader = EnvVarLoader.from_dict(name, var_dict)

        # When/Then
        with self.assertRaises(InvalidVariable):
            loader.load(None)


class TestTemplateVarLoader(unittest.TestCase):

    def test_validation_failure(self):
        name = 'template_var'
        var_dict = {
            'type': 'foo',
            'template': 'VAR',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            TemplateVarLoader.from_dict(name, var_dict)

        name = 'template_var'
        var_dict = {
            'type': 'template',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            TemplateVarLoader.from_dict(name, var_dict)

        # Given
        var_dict = {
            'template': '{foo}',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            TemplateVarLoader.from_dict(name, var_dict)

    def test_template_no_substitutions(self):
        # Given
        name = 'templated'
        value = '/some/path'
        var_dict = {
            'type': 'template',
            'template': value,
        }
        loader = TemplateVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load({})

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)

    def test_template_missing_substitution(self):
        # Given
        name = 'templated'
        var_dict = {
            'type': 'template',
            'template': '{temp}/path',
        }
        loader = TemplateVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load({})

        # Then
        self.assertFalse(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, None)

    def test_template_one_substitution(self):
        # Given
        name = 'templated'
        value = '/some/path'
        var_dict = {
            'type': 'template',
            'template': '{temp}/path',
        }
        loader = TemplateVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load({'temp': '/some'})

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)

    def test_template_chained_substitutions(self):
        # Given
        name = 'templated'
        value = '/some/other/path'
        var_dict = {
            'type': 'template',
            'template': '{temp}/path',
        }
        loader = TemplateVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load({'temp': '{prefix}/other'})

        # Then
        self.assertFalse(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader._template, '{prefix}/other/path')
        self.assertEqual(loader.value, None)

        # When
        is_loaded = loader.load({'prefix': '/some'})

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)


class TestVarLoader(unittest.TestCase):

    def test_var_loader(self):
        # Given
        var_dict = {
            'simple': '/path/prefix',
            'templated': {
                'type': 'template',
                'template': '{simple}/suffix',
            },
            'from_env': {
                'type': 'env',
                'env': 'SOME_VAR',
            },
        }
        loader = VarLoader(__file__)
        env_value = 'Var from env'
        expected = {
            'simple': '/path/prefix',
            'templated': '/path/prefix/suffix',
            'from_env': env_value,
        }

        # When
        with environment(SOME_VAR=env_value):
            variables = loader.load_variables(var_dict)

        # Then
        self.assertEqual(variables, expected)

    def test_template_loop(self):
        # Given
        var_dict = {
            'templated': {
                'type': 'template',
                'template': '{other_template}/something',
            },
            'other_template': {
                'type': 'template',
                'template': '{template}/other_thing',
            },
        }
        loader = VarLoader(__file__)

        # When/Then
        with self.assertRaises(VariableLoopError):
            loader.load_variables(var_dict)

    def test_unknown_variable_type(self):
        # Given
        var_dict = {
            'unknown': {
                'type': 'unknown',
            },
        }
        loader = VarLoader(__file__)

        # When/Then
        with self.assertRaises(InvalidVariableType):
            loader.load_variables(var_dict)

    def test_invalid_type_in_var_dict(self):
        # Given
        var_dict = {'unknown': []}
        loader = VarLoader(__file__)

        # When/Then
        with self.assertRaises(InvalidVariable):
            loader.load_variables(var_dict)

    def test_missing_variable_type(self):
        # Given
        var_dict = {
            'unknown': {},
        }
        loader = VarLoader(__file__)

        # When/Then
        with self.assertRaises(InvalidVariableType):
            loader.load_variables(var_dict)

    def test_load_variable(self):
        # Given
        variables = {
            'var1': 'foo',
            'var2': 'bar',
        }
        loader = VarLoader(__file__)
        to_load = {'type': 'template', 'template': '/{var1}/{var2}'}
        expected = '/foo/bar'

        # When
        value = loader.load_variable('name', to_load, variables)

        # Then
        self.assertEqual(value, expected)

    def test_load_variable_missing_template(self):
        # Given
        variables = {
            'var1': 'foo',
        }
        loader = VarLoader(__file__)
        to_load = {'type': 'template', 'template': '/{var1}/{var2}'}

        # When/Then
        with self.assertRaises(InvalidVariable):
            loader.load_variable('name', to_load, variables)

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

from ..exceptions import (
    InvalidVariable, InvalidVariableType, VariableLoopError)
from ..var_loader import (
    StringVarLoader, EnvVarLoader, TemplateVarLoader, VarLoader)


@contextmanager
def environment(**env):
    old_env = os.environ
    new_env = os.environ.copy()
    new_env.update(env)
    os.environ = new_env
    try:
        yield
    finally:
        os.environ = old_env


class TestStringVarLoader(unittest.TestCase):

    def test_string_loader(self):
        # Given
        loader = StringVarLoader('name', 'value')

        # Then
        self.assertTrue(loader.load(None))
        self.assertEqual(loader.name, 'name')
        self.assertEqual(loader.value, 'value')


class TestEnvVarLoader(unittest.TestCase):

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

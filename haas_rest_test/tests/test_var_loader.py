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
    InvalidVariable, InvalidVariableType, VariableLoopError)
from ..var_loader import StringVarLoader, VarLoader


class TestStringVarLoader(unittest.TestCase):

    def test_string_loader(self):
        # Given
        loader = StringVarLoader('name', 'value')

        # Then
        self.assertTrue(loader.load(None))
        self.assertEqual(loader.name, 'name')
        self.assertEqual(loader.value, 'value')


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

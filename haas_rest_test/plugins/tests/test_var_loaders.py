# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from haas.testing import unittest

from haas_rest_test.exceptions import InvalidVariable, YamlParseError
from haas_rest_test.tests.utils import environment
from ..var_loaders import EnvVarLoader, TemplateVarLoader


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

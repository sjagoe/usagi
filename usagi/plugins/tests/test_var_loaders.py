# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os
import json
import shutil
import tempfile

import six
import yaml

from haas.testing import unittest

from usagi.exceptions import InvalidVariable, YamlParseError
from usagi.tests.utils import environment
from ..var_loaders import (
    EnvVarLoader, FileVarLoader, RefVarLoader, TemplateVarLoader)


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
            is_loaded = loader.load(__file__, None)

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
            loader.load(__file__, None)


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
        is_loaded = loader.load(__file__, {})

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
        is_loaded = loader.load(__file__, {})

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
        is_loaded = loader.load(__file__, {'temp': '/some'})

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
        is_loaded = loader.load(__file__, {'temp': '{prefix}/other'})

        # Then
        self.assertFalse(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader._template, '{prefix}/other/path')
        self.assertEqual(loader.value, None)

        # When
        is_loaded = loader.load(__file__, {'prefix': '/some'})

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)


class TestFileVarLoader(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='haas-rest-test-')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_file_doesnt_exist(self):
        # Given
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))

        var_dict = {
            'type': 'file',
            'file': filepath,
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When/Then
        with self.assertRaises(InvalidVariable):
            loader.load(__file__, {})

    def test_load_relative_path(self):
        # Given
        data = '\ntest data\t\n  '
        expected = 'test data'
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        test_filepath = os.path.abspath(
            os.path.join(self.tempdir, 'test.txt'))
        with open(filepath, 'w') as fh:
            fh.write(data)

        var_dict = {
            'type': 'file',
            'file': 'file',
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(test_filepath, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, expected)

    def test_load_bad_relative_path(self):
        # Given
        data = '\ntest data\t\n  '
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        test_filepath = os.path.abspath(
            os.path.join(self.tempdir, 'test.txt'))
        with open(filepath, 'w') as fh:
            fh.write(data)

        var_dict = {
            'type': 'file',
            'file': 'dont_exist',
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When/Then
        with self.assertRaises(InvalidVariable):
            loader.load(test_filepath, {})

    def test_load_plain_file_strip(self):
        # Given
        data = '\ntest data\t\n  '
        expected = 'test data'
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        with open(filepath, 'w') as fh:
            fh.write(data)

        var_dict = {
            'type': 'file',
            'file': filepath,
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, expected)

    def test_load_plain_file_no_strip(self):
        # Given
        data = '\ntest data\t\n  '
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        with open(filepath, 'w') as fh:
            fh.write(data)

        var_dict = {
            'type': 'file',
            'file': filepath,
            'strip': False,
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, data)

    def test_load_json_file(self):
        # Given
        data = {'some': ['json', 'structure']}
        expected = data
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        with open(filepath, 'w') as fh:
            fh.write(json.dumps(data))

        var_dict = {
            'type': 'file',
            'file': filepath,
            'format': 'json',
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, expected)

    @unittest.skipIf(six.PY3, 'Yaml/Unicode and Python version issues')
    def test_load_yaml_file_py2(self):
        # Given
        data = {'some'.encode('ascii'):
                ['yaml'.encode('ascii'), 'structure'.encode('ascii')]}
        expected = data
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file.json'))
        with open(filepath, 'w') as fh:
            fh.write(yaml.dump(data, default_flow_style=False))

        var_dict = {
            'type': 'file',
            'file': filepath,
            'format': 'yaml',
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, expected)

    @unittest.skipIf(six.PY2, 'Yaml/Unicode and Python version issues')
    def test_load_yaml_file_py3(self):
        # Given
        data = {'some': ['yaml', 'structure']}
        expected = data
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file.json'))
        with open(filepath, 'w') as fh:
            fh.write(yaml.dump(data, default_flow_style=False))

        var_dict = {
            'type': 'file',
            'file': filepath,
            'format': 'yaml',
        }

        loader = FileVarLoader.from_dict('name', var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertEqual(is_loaded, True)
        self.assertEqual(loader.value, expected)

    def test_unknown_format(self):
        # Given
        data = 'csv,file'
        filepath = os.path.abspath(os.path.join(self.tempdir, 'file'))
        with open(filepath, 'w') as fh:
            fh.write(data)

        var_dict = {
            'type': 'file',
            'file': filepath,
            'format': 'csv',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            FileVarLoader.from_dict('name', var_dict)


class TestRefVarLoader(unittest.TestCase):

    def test_validation_failure(self):
        name = 'ref_var'
        var_dict = {
            'type': 'foo',
            'var': 'VAR',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            RefVarLoader.from_dict(name, var_dict)

        name = 'ref_var'
        var_dict = {
            'type': 'ref',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            RefVarLoader.from_dict(name, var_dict)

        # Given
        var_dict = {
            'var': 'other_var',
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            RefVarLoader.from_dict(name, var_dict)

    def test_ref_var_loader_basic(self):
        # Given
        name = 'ref_var'
        var_dict = {
            'type': 'ref',
            'var': 'other_var',
        }
        value = 'Ref var value'
        loader = RefVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load(__file__, {'other_var': value})

        # Then
        self.assertTrue(is_loaded)
        self.assertEqual(loader.name, name)
        self.assertEqual(loader.value, value)

    def test_ref_var_loader_missing_reference(self):
        # Given
        name = 'ref_var'
        var_dict = {
            'type': 'ref',
            'var': 'other_var',
        }
        loader = RefVarLoader.from_dict(name, var_dict)

        # When
        is_loaded = loader.load(__file__, {})

        # Then
        self.assertFalse(is_loaded)
        self.assertEqual(loader.name, name)

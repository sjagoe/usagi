# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import textwrap

from haas.testing import unittest

from haas_rest_test.config import Config
from haas_rest_test.exceptions import InvalidVariable, YamlParseError
from ..test_parameters import (
    BodyTestParameter, HeadersTestParameter, MethodTestParameter)


class TestMethodTestParameter(unittest.TestCase):

    def test_load(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {'method': 'POST'}
        parameter = MethodTestParameter.from_dict(spec)

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, spec)

    def test_invalid_method(self):
        # Given
        spec = {'method': 'OTHER'}

        # When/Then
        with self.assertRaises(YamlParseError):
            MethodTestParameter.from_dict(spec)


class TestHeadersTestParameter(unittest.TestCase):

    def test_invalid_object(self):
        # Given
        spec = {'headers': 'a-string'}

        # When/Then
        with self.assertRaises(YamlParseError):
            HeadersTestParameter.from_dict(spec)

    def test_load(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {'headers': {'Content-Type': 'application/json'}}
        parameter = HeadersTestParameter.from_dict(spec)

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, spec)

    def test_load_variable(self):
        # Given
        config = Config.from_dict(
            {
                'host': 'name.domain',
                'vars': {
                    'some_var': 'application/json',
                },
            },
            __file__)
        spec = {
            'headers': {
                'Content-Type': {
                    'type': 'ref',
                    'var': 'some_var',
                },
            },
        }
        parameter = HeadersTestParameter.from_dict(spec)
        expected = {'headers': {'Content-Type': 'application/json'}}

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)

    def test_load_missing_variable(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {
            'headers': {
                'Content-Type': {
                    'type': 'ref',
                    'var': 'none',
                },
            },
        }
        parameter = HeadersTestParameter.from_dict(spec)

        # When/Then
        with self.assertRaises(InvalidVariable):
            with parameter.load(config):
                pass


class TestBodyTestParameter(unittest.TestCase):

    def test_invalid_object(self):
        # Given
        spec = {'body': 'a-string'}

        # When/Then
        with self.assertRaises(YamlParseError):
            BodyTestParameter.from_dict(spec)

    def test_body_json(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {
            'body': {
                'format': 'json',
                'lookup-var': False,
                'value': {'param': ['value1', 'value2']},
            },
        }
        parameter = BodyTestParameter.from_dict(spec)
        expected = {
            'headers': {'Content-Type': 'application/json'},
            'data': '{"param": ["value1", "value2"]}',
        }

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)

    def test_body_yaml(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {
            'body': {
                'format': 'yaml',
                'lookup-var': False,
                'value': {'param': ['value1', 'value2']},
            },
        }
        parameter = BodyTestParameter.from_dict(spec)
        expected = {
            'headers': {'Content-Type': 'application/yaml'},
            'data': textwrap.dedent(
                """\
                param:
                - value1
                - value2
                """
            ),
        }

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)

    def test_body_plain(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {
            'body': {
                'format': 'plain',
                'value': 'plaintext',
            },
        }
        parameter = BodyTestParameter.from_dict(spec)
        expected = {
            'headers': {'Content-Type': 'text/plain'},
            'data': 'plaintext',
        }

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)

    def test_body_format_none(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {
            'body': {
                'format': 'none',
                'lookup-var': False,
                'value': 'plaintext',
            },
        }
        parameter = BodyTestParameter.from_dict(spec)
        expected = {
            'data': 'plaintext',
        }

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)

    def test_body_from_var(self):
        # Given
        config = Config.from_dict(
            {
                'host': 'name.domain',
                'vars': {
                    'data': 'some-data',
                },
            },
            __file__)
        spec = {
            'body': {
                'format': 'plain',
                'value': {'type': 'ref', 'var': 'data'},
            },
        }
        parameter = BodyTestParameter.from_dict(spec)
        expected = {
            'headers': {'Content-Type': 'text/plain'},
            'data': 'some-data',
        }

        # When
        with parameter.load(config) as loaded:
            # Then
            self.assertEqual(loaded, expected)


class TestBodyTestParameterMultipart(unittest.TestCase):

    def test_create_multipart_body_loader(self):
        # Given
        multipart_body = {
            'data': {
                'Content-Type': 'text/plain',
                'value': 'some text',
            },
            'file': {
                'filename': 'some-file.zip',
            },
        }
        spec = {
            'body': {
                'format': 'multipart',
                'value': multipart_body,
            },
        }

        # When/Then (no validation error occurs)
        BodyTestParameter.from_dict(spec)

    def test_create_multipart_loader_missing_value(self):
        # Given
        multipart_body = {
            'data': {
                'Content-Type': 'text/plain',
            },
        }
        spec = {
            'body': {
                'format': 'multipart',
                'value': multipart_body,
            },
        }

        # When/Then
        with self.assertRaises(YamlParseError):
            BodyTestParameter.from_dict(spec)

    def test_create_multipart_loader_missing_form_content_type(self):
        # Given
        multipart_body = {
            'data': {
                'value': 'some text',
            },
        }
        spec = {
            'body': {
                'format': 'multipart',
                'value': multipart_body,
            },
        }

        # When/Then (no validation error occurs)
        with self.assertRaises(YamlParseError):
            BodyTestParameter.from_dict(spec)

    def test_create_multipart_form_data(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        expected1 = 'some text'
        expected2 = '{}'
        multipart_body = {
            'field1': {
                'Content-Type': 'text/plain',
                'value': expected1,
            },
            'field2': {
                'Content-Type': 'application/json',
                'value': expected2,
            },
        }
        spec = {
            'body': {
                'format': 'multipart',
                'value': multipart_body,
            },
        }

        loader = BodyTestParameter.from_dict(spec)

        # When
        with loader.load(config) as loaded:
            # Then
            self.assertIn('data', loaded)
            self.assertNotIn('headers', loaded)
            data = loaded['data']
            self.assertIn('field1', data)
            self.assertIn('field2', data)

            name, content, type_ = data['field1']
            self.assertEqual(name, '')
            self.assertEqual(content.read().decode('utf-8'), expected1)
            self.assertEqual(type_, 'text/plain; charset=UTF-8')

            name, content, type_ = data['field2']
            self.assertEqual(name, '')
            self.assertEqual(content.read().decode('utf-8'), expected2)
            self.assertEqual(type_, 'application/json; charset=UTF-8')

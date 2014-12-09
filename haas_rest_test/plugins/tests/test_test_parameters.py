# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from haas.testing import unittest

from haas_rest_test.config import Config
from haas_rest_test.exceptions import YamlParseError
from ..test_parameters import MethodTestParameter


class TestMethodTestParameter(unittest.TestCase):

    def test_load(self):
        # Given
        config = Config.from_dict({'host': 'name.domain'}, __file__)
        spec = {'method': 'POST'}
        parameter = MethodTestParameter.from_dict(spec)

        # When
        loaded = parameter.load(config)

        # Then
        self.assertEqual(loaded, spec)

    def test_invalid_method(self):
        # Given
        spec = {'method': 'OTHER'}

        # When/Then
        with self.assertRaises(YamlParseError):
            MethodTestParameter.from_dict(spec)

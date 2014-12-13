# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from haas.testing import unittest

from .utils import environment
from ..config import Config


class TestTemplateVariables(unittest.TestCase):

    def test_host_from_env_var(self):
        # Given
        config_dict = {
            'host': {
                'type': 'env',
                'env': 'ENV_VAR',
            },
        }
        expected = 'host.domain'

        # When
        with environment(ENV_VAR=expected):
            config = Config.from_dict(config_dict, __file__)

        # Then
        self.assertEqual(config.host, expected)

    def test_host_from_template(self):
        # Given
        config_dict = {
            'host': {
                'type': 'template',
                'template': '{var1}.domain',
            },
            'vars': {'var1': 'host'},
        }
        expected = 'host.domain'

        # When
        config = Config.from_dict(config_dict, __file__)

        # Then
        self.assertEqual(config.host, expected)

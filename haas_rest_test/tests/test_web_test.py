# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from six.moves import urllib

from haas.testing import unittest

from ..config import Config
from ..utils import create_session
from ..web_test import WebTest


class TestWebTest(unittest.TestCase):

    def test_from_spec(self):
        # Given
        config = Config('http', 'test.invalid')
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
        }
        expected_url = urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                config.scheme,
                config.host,
                url,
                None,
                None,
                None,
            ),
        )

        # When
        test = WebTest.from_test_spec(session, test_spec, config)

        # Then
        self.assertIs(test.session, session)
        self.assertIs(test.config, config)
        self.assertEqual(test.name, name)
        self.assertEqual(test.url, expected_url)
        self.assertEqual(test.method, 'GET')

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from haas.testing import unittest

from ..utils import create_session
from ..web_test import WebTest


class TestWebTest(unittest.TestCase):

    def test_from_spec(self):
        # Given
        session = create_session()
        name = 'A test'
        url = '/api/test'
        test_spec = {
            'name': name,
            'url': url,
        }

        # When
        test = WebTest.from_test_spec(session, test_spec)

        # Then
        self.assertIs(test.session, session)
        self.assertEqual(test.name, name)
        self.assertEqual(test.url, url)
        self.assertEqual(test.method, 'GET')

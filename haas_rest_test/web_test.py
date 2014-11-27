# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals


class WebTest(object):

    def __init__(self, session, name, method, url):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.method = method
        self.url = url

    @classmethod
    def from_test_spec(cls, session, spec):
        return cls(
            session=session,
            name=spec['name'],
            method=spec.get('method', 'GET'),
            url=spec['url'],
        )

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from six.moves import urllib


class WebTest(object):

    def __init__(self, session, config, name, method, path):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.method = method
        self.config = config
        self.path = path

    @property
    def url(self):
        return urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                self.config.scheme,
                self.config.host,
                self.path,
                None,
                None,
                None,
            ),
        )

    @classmethod
    def from_test_spec(cls, session, spec, config):
        return cls(
            session=session,
            config=config,
            name=spec['name'],
            method=spec.get('method', 'GET'),
            path=spec['url'],
        )

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from requests.exceptions import ConnectionError
from six.moves import urllib

from .exceptions import InvalidAssertionClass


def initialize_assertions(assertion_map, assertion_specs):
    for spec in assertion_specs:
        name = spec['name']
        cls = assertion_map.get(name)
        if cls is None:
            raise InvalidAssertionClass(name)
        yield cls.from_dict(spec)


class WebTest(object):

    def __init__(self, session, config, name, method, path, assertions):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.method = method
        self.config = config
        self.path = path
        self.assertions = assertions

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
    def from_dict(cls, session, spec, config, assertions_map):
        assertion_specs = spec.get('assertions', [])
        assertions = initialize_assertions(
            assertions_map, assertion_specs)
        return cls(
            session=session,
            config=config,
            name=spec['name'],
            method=spec.get('method', 'GET'),
            path=spec['url'],
            assertions=list(assertions),
        )

    def run(self, case):
        try:
            response = self.session.request(
                self.method, self.url,
            )
        except ConnectionError as exc:
            case.fail('Unable to connect: {!r}'.format(str(exc)))
        for assertion in self.assertions:
            assertion.run(case, response)

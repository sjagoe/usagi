# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from requests.exceptions import ConnectionError
from six.moves import urllib

from .exceptions import InvalidAssertionClass, InvalidVariableType


def initialize_assertions(assertion_map, assertion_specs):
    for spec in assertion_specs:
        name = spec['name']
        cls = assertion_map.get(name)
        if cls is None:
            raise InvalidAssertionClass(name)
        yield cls.from_dict(spec)


def _load_headers(headers_map, config):
    return dict(
        (header_name, config.load_variable(header_name, header_value))
        for header_name, header_value in headers_map.items()
    )


class WebTest(object):

    def __init__(self, session, config, name, method, path, headers,
                 assertions):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.method = method
        self.config = config
        self.path = path
        self.headers = headers
        self.assertions = assertions

    @property
    def url(self):
        return urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                self.config.scheme,
                self.config.host,
                self.config.load_variable('url', self.path),
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
            headers=_load_headers(spec.get('headers', {}), config),
            assertions=list(assertions),
        )

    def run(self, case):
        try:
            url = self.url
        except InvalidVariableType as exc:
            case.fail(repr(exc))
        try:
            response = self.session.request(
                self.method, url, headers=self.headers)
        except ConnectionError as exc:
            case.fail('{0!r}: Unable to connect: {1!r}'.format(url, str(exc)))
        for assertion in self.assertions:
            assertion.run(self.config, url, case, response)

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from requests.exceptions import ConnectionError
from six.moves import urllib

from .exceptions import (
    InvalidAssertionClass, InvalidParameterClass, InvalidVariableType)


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


def initialize_test_parameters(test_parameter_plugins, parameter_specs):
    for name, value in parameter_specs.items():
        cls = test_parameter_plugins.get(name)
        if cls is None:
            raise InvalidParameterClass(name)
        yield cls.from_dict({name: value})


class WebTest(object):

    def __init__(self, session, config, name, path, headers,
                 assertions, test_parameters):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.config = config
        self.path = path
        self.headers = headers
        self.assertions = assertions
        self.test_parameters = test_parameters

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

    @property
    def method(self):
        return self._get_test_parameters()['method']

    @classmethod
    def from_dict(cls, session, spec, config, assertions_map,
                  test_parameter_plugins):
        spec = spec.copy()
        name = spec.pop('name')

        assertion_specs = spec.pop('assertions', [])
        assertions = initialize_assertions(
            assertions_map, assertion_specs)
        test_parameters = initialize_test_parameters(
            test_parameter_plugins, spec.pop('parameters', {}))

        return cls(
            session=session,
            config=config,
            name=name,
            path=spec['url'],
            headers=_load_headers(spec.get('headers', {}), config),
            assertions=list(assertions),
            test_parameters=list(test_parameters),
        )

    def _get_test_parameters(self):
        parameters = {  # Parameter defaults
            'method': 'GET',
        }
        for test_parameter in self.test_parameters:
            parameters.update(test_parameter.load(self.config))
        return parameters

    def run(self, case):
        try:
            url = self.url
        except InvalidVariableType as exc:
            case.fail(repr(exc))

        test_parameters = self._get_test_parameters()

        try:
            response = self.session.request(
                url=url, headers=self.headers, **test_parameters)
        except ConnectionError as exc:
            case.fail('{0!r}: Unable to connect: {1!r}'.format(url, str(exc)))
        for assertion in self.assertions:
            assertion.run(self.config, url, case, response)

# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager

from requests.exceptions import ConnectionError
from six.moves import urllib

from .exceptions import (
    InvalidAssertionClass, InvalidParameterClass, InvalidVariableType)
from .parameter_builder import ParameterBuilder


def initialize_assertions(assertion_map, assertion_specs):
    for spec in assertion_specs:
        name = spec['name']
        cls = assertion_map.get(name)
        if cls is None:
            raise InvalidAssertionClass(name)
        yield cls.from_dict(spec)


def initialize_test_parameter_loaders(test_parameter_plugins, parameter_specs):
    for name, value in parameter_specs.items():
        cls = test_parameter_plugins.get(name)
        if cls is None:
            raise InvalidParameterClass(name)
        yield cls.from_dict({name: value})


_Default = object()


class WebTest(object):
    """The main entry-point into a single web test case.

    The :meth:`WebTest.run() <usagi.web_test.WebTest.run>`
    method is executed from within the generated TestCase test method.

    """

    def __init__(self, session, config, name, path, assertions,
                 parameter_loaders, max_diff):
        super(WebTest, self).__init__()
        self.session = session
        self.name = name
        self.config = config
        self.path = path
        self.assertions = assertions
        self.parameter_loaders = parameter_loaders
        self.max_diff = max_diff

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

    @contextmanager
    def test_parameters(self):
        config = self.config
        parameter_loaders = self.parameter_loaders
        with ParameterBuilder(config, parameter_loaders) as test_parameters:
            yield test_parameters

    @classmethod
    def from_dict(cls, session, spec, config, assertions_map,
                  test_parameter_plugins):
        """Create a :class:`~.WebTest` from a test specification.

        """
        spec = spec.copy()
        name = spec.pop('name')

        max_diff = spec.pop('max-diff', _Default)

        assertion_specs = spec.pop('assertions', [])
        assertions = initialize_assertions(
            assertions_map, assertion_specs)
        parameter_loaders = initialize_test_parameter_loaders(
            test_parameter_plugins, spec.pop('parameters', {}))

        poll_config = spec.pop('poll', None)

        if poll_config is not None:
            timeout = poll_config['timeout']
            period = poll_config['period']
            cls = lambda **k: WebPoll(period=period, timeout=timeout, **k)

        return cls(
            session=session,
            config=config,
            name=name,
            path=spec['url'],
            assertions=list(assertions),
            parameter_loaders=list(parameter_loaders),
            max_diff=max_diff,
        )

    def run(self, case):
        """Execute the web test case, and record results via the ``case``.

        Parameters
        ----------
        case : unittest.TestCase
            The ``TestCase`` instance used to record test results.

        """
        if self.max_diff is not _Default:
            case.maxDiff = self.max_diff

        try:
            url = self.url
        except InvalidVariableType as exc:
            case.fail(repr(exc))

        with self.test_parameters() as test_parameters:
            try:
                response = self.session.request(url=url, **test_parameters)
            except ConnectionError as exc:
                case.fail('{0!r}: Unable to connect: {1!r}'.format(
                    url, str(exc)))

        for assertion in self.assertions:
            assertion.run(self.config, url, case, response)


class WebPoll(WebTest):
    """
    A test type that allows polling.

    """

    def __init__(self, period, timeout, **args):
        """
        Parameters
        ----------
        period : int
            The number of seconds between poll attempts.
        timeout : int
            Total amount of time to poll before failure.

        """
        super(WebPoll, self).__init__(**args)
        self._period = period
        self._timeout = timeout

    def run(self, case):
        import time
        from timeit import default_timer
        run_poll = lambda: super(WebPoll, self).run(case)
        start_time = default_timer()
        while True:
            try:
                run_poll()
            except case.failureException:
                now = default_timer()
                duration = now - start_time
                if duration >= self._timeout:
                    raise
                time.sleep(self._period)
            else:
                return

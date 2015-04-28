# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import logging
import sys

from jsonschema.exceptions import ValidationError
from stevedore.extension import ExtensionManager
import jsonschema
import six
import yaml

from haas.module_import_error import ModuleImportError
from haas.testing import unittest

from .config import Config
from .exceptions import YamlParseError
from .schema import SCHEMA
from .utils import create_session
from .web_test import WebTest


logger = logging.getLogger(__name__)


TEST_NAME_ATTRIBUTE = 'usagi_name'


def _create_yaml_parse_error_test(filename, error):
    message = 'Unable to parse test {0!r}\n{1}'.format(
        error, error)

    def test_error(self):
        raise YamlParseError(message)

    method_name = 'test_error'
    cls = type(ModuleImportError.__name__,
               (ModuleImportError, unittest.TestCase,),
               {method_name: test_error})
    return cls(method_name)


def _create_test_method(test):
    def test_method(self):
        test.run(self)

    setattr(test_method, TEST_NAME_ATTRIBUTE, test.name)

    return test_method


def _create_reused_tests(session, config, assertions_map,
                         test_parameter_plugins, test_names, test_definitions):
    return [
        WebTest.from_dict(
            session, spec, config, assertions_map,
            test_parameter_plugins)
        for name in test_names
        for spec in test_definitions[name]
    ]


def create_test_case_for_case(filename, config, case, assertions_map,
                              test_parameter_plugins, test_definitions):
    """Programatically generate ``TestCases`` from a test specification.

    Returns
    -------
    test_case_cls : type
        A subclass of ``unittest.TestCase`` containing all of the
        generated tests, in the same order as defined in the file.

    """
    session = create_session()

    pre_run_cases = _create_reused_tests(
        session, config, assertions_map, test_parameter_plugins,
        case.get('case-setup', []), test_definitions)
    post_run_cases = _create_reused_tests(
        session, config, assertions_map, test_parameter_plugins,
        case.get('case-teardown', []), test_definitions)
    tests = pre_run_cases + [
        WebTest.from_dict(
            session, spec, config, assertions_map, test_parameter_plugins)
        for spec in case['tests']
    ] + post_run_cases
    test_count = len(tests)
    class_dict = dict(
        ('test_{index:0>{test_count}}'.format(
            index=index, test_count=test_count),
         _create_test_method(test))
        for index, test in enumerate(tests)
    )
    class_dict[TEST_NAME_ATTRIBUTE] = case['name']

    if 'max-diff' in case:
        class_dict['maxDiff'] = case['max-diff']

    def __str__(self):
        method = getattr(self, self._testMethodName)
        template = '{0!r} ({1})'
        test_name = '{0}:{1}'.format(getattr(self, TEST_NAME_ATTRIBUTE),
                                     getattr(method, TEST_NAME_ATTRIBUTE))
        str_filename = filename
        if six.PY2:
            encoding = sys.getdefaultencoding()
            template = template.encode(encoding)
            test_name = test_name.encode(encoding)
            if isinstance(str_filename, six.text_type):
                str_filename = filename.encode(encoding)
        return template.format(
            test_name,
            str_filename,
        )

    class_dict['__str__'] = __str__

    class_name = 'GeneratedYamlTestCase'
    if six.PY2:
        class_name = class_name.encode('ascii')
    return type(class_name, (unittest.TestCase,), class_dict)


class YamlTestLoader(object):
    """A test case generator, creating ``TestCase`` and ``TestSuite``
    instances from a single YAML file.

    Parameters
    ----------
    loader : haas.loader.Loader
        The ``haas`` test loader.

    """

    def __init__(self, loader):
        super(YamlTestLoader, self).__init__()
        self._loader = loader

        assertions = ExtensionManager(
            namespace='usagi.assertions',
        )
        test_parameters = ExtensionManager(
            namespace='usagi.parameters'
        )

        self._assertions_map = dict(
            (name, assertions[name].plugin)
            for name in assertions.names()
        )
        self._test_parameters = dict(
            (name, test_parameters[name].plugin)
            for name in test_parameters.names()
        )

    def load_tests_from_file(self, filename):
        """Load the YAML test file and create a ``TestSuite`` containing all
        test cases contained in the file.

        """
        with open(filename) as fh:
            test_structure = yaml.safe_load(fh)
        return self.load_tests_from_yaml(test_structure, filename)

    def load_tests_from_yaml(self, test_structure, filename):
        """Create a ``TestSuite`` containing all test cases contained in the
        yaml structure.

        """
        loader = self._loader
        try:
            jsonschema.validate(test_structure, SCHEMA)
        except ValidationError as e:
            test = _create_yaml_parse_error_test(filename, str(e))
            return loader.create_suite([test])
        config = Config.from_dict(test_structure['config'], filename)

        test_pre_definitions = test_structure.get('test-pre-definitions', {})

        cases = (
            create_test_case_for_case(
                filename, config, case, self._assertions_map,
                self._test_parameters, test_pre_definitions)
            for case in test_structure['cases']
        )
        tests = [loader.load_case(case) for case in cases]
        return loader.create_suite(tests)

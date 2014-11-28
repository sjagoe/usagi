# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import logging

from jsonschema.exceptions import ValidationError
import jsonschema
import six
from stevedore.extension import ExtensionManager
import yaml

from haas.module_import_error import ModuleImportError
from haas.testing import unittest

from .config import Config
from .exceptions import YamlParseError
from .schema import SCHEMA
from .utils import create_session
from .web_test import WebTest


logger = logging.getLogger(__name__)


TEST_NAME_ATTRIBUTE = 'haas_rest_test_name'


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

    test_method.__doc__ = test.name

    return test_method


def create_test_case_for_case(filename, config, case, assertions_map):
    session = create_session()

    tests = [WebTest.from_dict(session, spec, config, assertions_map)
             for spec in case['tests']]
    class_dict = dict(
        ('test_{0}'.format(index), _create_test_method(test))
        for index, test in enumerate(tests)
    )
    class_dict[TEST_NAME_ATTRIBUTE] = case['name']

    def __str__(self):
        return '{0} ({1})'.format(
            getattr(self, TEST_NAME_ATTRIBUTE),
            filename,
        )

    class_dict['__str__'] = __str__

    class_name = 'GeneratedYamlTestCase'
    if six.PY2:
        class_name = class_name.encode('ascii')
    return type(class_name, (unittest.TestCase,), class_dict)


class YamlTestLoader(object):

    def __init__(self, loader):
        super(YamlTestLoader, self).__init__()
        self._loader = loader
        assertions = ExtensionManager(
            namespace='haas_rest_test.assertions',
        )
        self._assertions_map = dict(
            (name, assertions[name].plugin)
            for name in assertions.names()
        )

    def load_tests_from_file(self, filename):
        with open(filename) as fh:
            test_structure = yaml.safe_load(fh)
        return self.load_tests_from_yaml(test_structure, filename)

    def load_tests_from_yaml(self, test_structure, filename):
        loader = self._loader
        try:
            jsonschema.validate(test_structure, SCHEMA)
        except ValidationError as e:
            test = _create_yaml_parse_error_test(filename, str(e))
            return loader.create_suite([test])
        config = Config.from_dict(test_structure['config'])
        cases = (
            create_test_case_for_case(
                filename, config, case, self._assertions_map)
            for case in test_structure['cases']
        )
        tests = [loader.load_case(case) for case in cases]
        return loader.create_suite(tests)

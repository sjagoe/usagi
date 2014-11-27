# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import logging

from jsonschema.exceptions import ValidationError
from requests.utils import default_user_agent as requests_user_agent
import jsonschema
import requests
import yaml

from haas.module_import_error import ModuleImportError
from haas.testing import unittest

import haas_rest_test
from .exceptions import YamlParseError
from .schema import SCHEMA


logger = logging.getLogger(__name__)


TEST_NAME_ATTRIBUTE = 'haas_rest_test_name'


def haas_rest_test_user_agent():
    return 'haas-rest-test/{0} {1}'.format(
        haas_rest_test.__version__, requests_user_agent())


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


def _create_test_method(requests_session, test_spec):
    def test_method(self):
        self.fail()

    test_method.__doc__ = test_spec['name']

    return test_method


def create_test_case_for_group(filename, group):
    session = requests.Session()
    session.headers['User-Agent'] = haas_rest_test_user_agent()

    class_dict = dict(
        ('test_{0}'.format(index), _create_test_method(session, spec))
        for index, spec in enumerate(group['tests'])
    )
    class_dict[TEST_NAME_ATTRIBUTE] = group['name']

    def __str__(self):
        return '{0} ({1})'.format(
            getattr(self, TEST_NAME_ATTRIBUTE),
            filename,
        )

    class_dict['__str__'] = __str__

    return type('GeneratedYamlTestCase', (unittest.TestCase,), class_dict)


class YamlTestLoader(object):

    def __init__(self, loader):
        super(YamlTestLoader, self).__init__()
        self._loader = loader

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
        cases = (
            create_test_case_for_group(filename, group)
            for group in test_structure['groups']
        )
        tests = [loader.load_case(case) for case in cases]
        return loader.create_suite(tests)

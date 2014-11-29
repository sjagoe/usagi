# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import logging
import os

from haas.plugins.discoverer import match_path

from .yaml_test_loader import YamlTestLoader

logger = logging.getLogger(__name__)


class RestTestDiscoverer(object):

    def __init__(self, loader, **kwargs):
        super(RestTestDiscoverer, self).__init__(**kwargs)
        self._loader = loader
        self._yaml_loader = YamlTestLoader(loader)

    def discover(self, start, top_level_directory=None, pattern=None):
        """Discover YAML-formatted Web API tests.

        Parameters
        ----------
        start : str
            Directory from which to recursively discover test cases.
        top_level_directory : None
            Ignored; for API compatibility with haas.
        pattern : None
            Ignored; for API compatibility with haas.

        """
        if os.path.isdir(start):
            start_directory = start
            return self._discover_by_directory(start_directory)
        elif os.path.isfile(start):
            start_filepath = start
            return self._discover_by_file(start_filepath)
        return self._loader.create_suite()

    def _discover_by_directory(self, start_directory):
        """Run test discovery in a directory.

        Parameters
        ----------
        start_directory : str
            The package directory in which to start test discovery.

        """
        start_directory = os.path.abspath(start_directory)
        tests = self._discover_tests(start_directory)
        return self._loader.create_suite(list(tests))

    def _discover_by_file(self, start_filepath):
        """Run test discovery on a single file.

        Parameters
        ----------
        start_filepath : str
            The module file in which to start test discovery.

        """
        start_filepath = os.path.abspath(start_filepath)
        logger.debug('Discovering tests in file: start_filepath=%r',
                     start_filepath)

        tests = self._load_from_file(start_filepath)
        return self._loader.create_suite(list(tests))

    def _load_from_file(self, filepath):
        logger.debug('Loading tests from %r', filepath)
        tests = self._yaml_loader.load_tests_from_file(filepath)
        return self._loader.create_suite(tests)

    def _discover_tests(self, start_directory):
        pattern = '*.yml'
        for curdir, dirnames, filenames in os.walk(start_directory):
            logger.debug('Discovering tests in %r', curdir)
            for filename in filenames:
                filepath = os.path.join(curdir, filename)
                if not match_path(filename, filepath, pattern):
                    logger.debug('Skipping %r', filepath)
                    continue
                yield self._load_from_file(filepath)

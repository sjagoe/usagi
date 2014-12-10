# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from requests.utils import default_user_agent as requests_user_agent
import requests

import haas_rest_test


def haas_rest_test_user_agent():
    return 'haas-rest-test/{0} {1}'.format(
        haas_rest_test.__version__, requests_user_agent())


def create_session():
    session = requests.Session()
    session.headers['User-Agent'] = haas_rest_test_user_agent()
    return session

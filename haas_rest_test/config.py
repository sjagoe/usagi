# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals


class Config(object):

    def __init__(self, scheme, host):
        super(Config, self).__init__()
        self.scheme = scheme
        self.host = host

    @classmethod
    def from_dict(cls, config):
        return cls(
            scheme=config.get('scheme', 'http'),
            host=config['host'],
        )

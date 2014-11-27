# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals


class StatusCodeAssertion(object):

    _schema = {
    }

    def __init__(self, valid_codes):
        super(StatusCodeAssertion, self).__init__()
        self.valid_codes = valid_codes

    @classmethod
    def from_dict(cls, data):
        # FIXME: Validate input with jsonschema
        return cls(valid_codes=data['expected'])

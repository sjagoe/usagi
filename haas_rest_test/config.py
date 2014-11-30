# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from .var_loader import VarLoader


class Config(object):

    def __init__(self, scheme, host, variables, var_loader):
        super(Config, self).__init__()
        self.var_loader = var_loader
        self.scheme = scheme
        self.variables = variables
        self.host = self.load_variable('host', host)

    @classmethod
    def from_dict(cls, config, test_filename):
        var_loader = VarLoader(test_filename)
        variables = var_loader.load_variables(config.get('vars', {}))
        return cls(
            scheme=config.get('scheme', 'http'),
            host=config['host'],
            variables=variables,
            var_loader=var_loader,
        )

    def load_variable(self, name, var):
        return self.var_loader.load_variable(name, var, self.variables)

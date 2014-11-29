# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os

from six import string_types


VAR = 'var'
ENV = 'env'
TEMPLATE = 'template'


def _dict_to_var(var_dict):
    if TEMPLATE in var_dict:
        return TEMPLATE, var_dict[TEMPLATE]
    elif ENV in var_dict:
        return ENV, var_dict[ENV]
    raise RuntimeError()


def _fill_template(name, value, template_vars):
    if isinstance(value, string_types):
        return VAR, name, value
    elif isinstance(value, dict):
        type_, value = _dict_to_var(value)
        if type_ == ENV:
            new_value = os.environ[value]  # KeyError
            return VAR, name, new_value
        elif type_ == TEMPLATE:
            try:
                new_value = value.format(**template_vars)
            except KeyError:
                return TEMPLATE, name, value
            if new_value == value:
                return VAR, name, new_value
            else:
                return TEMPLATE, name, new_value
        else:
            raise RuntimeError('Can\'t handle var {!r} of type: {!r}'.format(
                name, type_))
    else:
        raise RuntimeError('Can\'t handle var {!r}: {!r}'.format(name, value))


# FIXME: Very inefficient!
def template_variables(variables):
    if variables is None:
        return {}
    templated = {}
    templates = variables.copy()
    while len(templates) > 0:
        for name in templates.copy():
            value = templates.pop(name)
            type_, name, new_value = _fill_template(
                name, value, templated)
            if type_ == VAR:
                templated[name] = new_value
            elif type_ == TEMPLATE:
                templates[name] = {TEMPLATE: new_value}

    return templated


class Config(object):

    def __init__(self, scheme, host, variables):
        super(Config, self).__init__()
        self.scheme = scheme
        self.host = host
        self.variables = variables

    @classmethod
    def from_dict(cls, config):
        return cls(
            scheme=config.get('scheme', 'http'),
            host=config['host'],
            variables=template_variables(config.get('vars')),
        )

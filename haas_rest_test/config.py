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
    raise RuntimeError('Unknown var type {!r}'.format(var_dict))


def _resolve_simple_var(value):
    if isinstance(value, string_types):
        return VAR, value
    elif isinstance(value, dict):
        type_, value = _dict_to_var(value)
        if type_ == ENV:
            return VAR, os.environ[value]  # KeyError
        else:
            return type_, value


def _resolve_simple_vars(variables):
    simple_vars = {}
    for name, var in variables.items():
        type_, value = _resolve_simple_var(var)
        if type_ != VAR:
            continue
        simple_vars[name] = value
    return simple_vars


def _fill_template(name, value, template_vars):
    type_, value = _dict_to_var(value)
    if type_ == TEMPLATE:
        try:
            new_value = value.format(**template_vars)
        except KeyError:  # We don't have all dependencies resolved yet
            return TEMPLATE, name, value
        else:
            try:
                new_value.format()
            except KeyError:  # We don't have all dependencies resolved yet
                return TEMPLATE, name, new_value
            else:
                return VAR, name, new_value
    else:
        raise RuntimeError('Can\'t handle var {!r} of type: {!r}'.format(
            name, type_))


def template_variables(variables):
    if variables is None:
        return {}
    templated = _resolve_simple_vars(variables)
    templates = dict((name, value) for name, value in variables.items()
                     if name not in templated)
    while len(templates) > 0:
        template_keys = set(templates.keys())
        for name in sorted(list(templates)):
            value = templates.pop(name)
            type_, name, new_value = _fill_template(
                name, value, templated)
            if type_ == VAR:
                templated[name] = new_value
            elif type_ == TEMPLATE:
                templates[name] = {TEMPLATE: new_value}
        if template_keys == set(templates.keys()):
            raise RuntimeError('Loop detected in template vars')

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

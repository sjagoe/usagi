# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import json
import os

from six import string_types

from .exceptions import InvalidVariable, VariableLoopError


VAR = 'var'
ENV = 'env'
FILE = 'file'
TEMPLATE = 'template'


def _var_from_file(test_filename, file, format='plain', **kwargs):
    if not os.path.isabs(file):
        file = os.path.join(os.path.dirname(test_filename), file)
    file = os.path.normpath(os.path.abspath(file))
    with open(file) as fh:
        data = fh.read()
    if format == 'plain':
        return data
    elif format == 'json':
        return json.loads(data)
    raise InvalidVariable(file)


def _dict_to_var(var_dict, filename):
    if TEMPLATE in var_dict:
        return TEMPLATE, var_dict[TEMPLATE]
    elif ENV in var_dict:
        return VAR, os.environ[var_dict[ENV]]  # KeyError
    elif FILE in var_dict:
        return VAR, _var_from_file(filename, **var_dict)
    raise InvalidVariable(repr(var_dict))


def _resolve_simple_var(value, filename):
    if isinstance(value, string_types):
        return VAR, value
    elif isinstance(value, dict):
        type_, value = _dict_to_var(value, filename)
        return type_, value


def _resolve_simple_vars(variables, filename):
    simple_vars = {}
    for name, var in variables.items():
        type_, value = _resolve_simple_var(var, filename)
        if type_ != VAR:
            continue
        simple_vars[name] = value
    return simple_vars


def _fill_template(name, value, template_vars):
    value = value[TEMPLATE]
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


def _template_variables(variables, filename):
    if variables is None:
        return {}
    templated = _resolve_simple_vars(variables, filename)
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
            raise VariableLoopError(
                'Loop detected in template vars: {0!r}'.format(template_keys))

    return templated


class Config(object):

    def __init__(self, scheme, host, variables, test_filename):
        super(Config, self).__init__()
        self.test_filename = test_filename
        self.scheme = scheme
        self.variables = variables
        self.host = self.fill_template(host)

    @classmethod
    def from_dict(cls, config, test_filename):
        return cls(
            scheme=config.get('scheme', 'http'),
            host=config['host'],
            variables=_template_variables(config.get('vars'), test_filename),
            test_filename=test_filename,
        )

    def fill_template(self, template):
        type_, value = _resolve_simple_var(template, self.test_filename)
        if type_ == VAR:
            return value
        elif type_ == TEMPLATE:
            return value.format(**self.variables)

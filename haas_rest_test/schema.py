# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'title': 'Haas Rest Test test cases',
    'description': 'Test case markup for Haas Rest Test',
    'type': 'object',
    'properties': {
        'version': {
            'type': 'string',
        },
        'config': {
            'type': 'object',
            'description': 'Configuration applied to all generated test cases',
            'properties': {
                'vars': {'type': 'object'},
                'scheme': {
                    'enum': ['http', 'https'],
                    'default': 'http',
                },
                'host': {
                    'oneOf': [
                        {'$ref': '#/definitions/env_var'},
                        {'$ref': '#/definitions/simple_var'},
                        {'$ref': '#/definitions/template_var'},
                    ],
                },
            },
            'required': ['host'],
        },
        'cases': {
            'type': 'array',
            'items': {'$ref': '#/definitions/case'},
        },
    },
    'required': ['version', 'config', 'cases'],
    'definitions': {
        'name': {
            'description': 'The name of the object',
            'type': 'string',
        },
        'env_var': {
            'type': 'object',
            'properties': {
                'env': {
                    'type': 'string',
                },
            },
            'required': ['env'],
        },
        'template_var': {
            'type': 'object',
            'properties': {
                'template': {
                    'type': 'string',
                },
            },
            'required': ['template'],
        },
        'simple_var': {
            'type': 'string',
        },
        'case': {
            'type': 'object',
            'description': 'A grouping of test cases',
            'properties': {
                'name': {
                    '$ref': '#/definitions/name',
                },
                'tests': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/test',
                    },
                    'minItems': 1,
                },
            },
            'required': ['name', 'tests'],
        },
        'test': {
            'type': 'object',
            'properties': {
                'method': {
                    'enum': ['GET', 'POST', 'DELETE', 'PUT', 'HEAD'],
                    'default': 'GET',
                },
                'url': {
                    'oneOf': [
                        {'$ref': '#/definitions/simple_var'},
                        {'$ref': '#/definitions/template_var'},
                    ],
                },
                'name': {
                    '$ref': '#/definitions/name',
                },
                'assertions': {
                    'type': 'array',
                    'minItems': 1,
                },
            },
            'required': ['url', 'name'],
        },
    },
}

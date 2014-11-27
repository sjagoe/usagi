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
                'variables': {'type': 'object'},
                'scheme': {
                    'enum': ['http', 'https'],
                    'default': 'http',
                },
                'host': {
                    'type': 'string',
                },
            },
            'required': ['host'],
        },
        'groups': {
            'type': 'array',
            'items': {'$ref': '#/definitions/group'},
        },
    },
    'required': ['version', 'config', 'groups'],
    'definitions': {
        'name': {
            'description': 'The name of the object',
            'type': 'string',
        },
        'url_template': {
            'type': 'object',
            'properties': {
                'template': {
                    'type': 'string',
                },
            },
        },
        'url': {
            'type': 'string',
        },
        'group': {
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
                        {'$ref': '#/definitions/url'},
                        {'$ref': '#/definitions/url_template'},
                    ],
                },
                'name': {
                    '$ref': '#/definitions/name',
                },
            },
            'required': ['url', 'name'],
        },
    },
}

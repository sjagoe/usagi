# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
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
        'test-pre-definitions': {
            'type': 'object',
            'patternProperties': {
                '^.*$': {
                    'type': 'array',
                    'items': {'$ref': '#/definitions/test'},
                    'minItems': 1,
                },
            },
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
        'file_var': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'description': 'Filename relative to the current YAML file.',  # noqa
                },
                'format': {
                    'enum': ['plain', 'json'],
                    'default': 'plain',
                },
            },
            'required': ['name'],
        },
        'simple_var': {
            'type': 'string',
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
        'case': {
            'type': 'object',
            'description': 'A grouping of test cases',
            'properties': {
                'name': {
                    '$ref': '#/definitions/name',
                },
                'case-setup': {
                    'description': 'References to items in test-pre-definitions that will run before any tests defined in this case',  # noqa
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
                'case-teardown': {
                    'description': 'References to items in test-pre-definitions that will run after all tests defined in this case',  # noqa
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
                'tests': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/test',
                    },
                    'minItems': 1,
                },
                'max-diff': {
                    '$ref': '#/definitions/max-diff',
                },
            },
            'required': ['name', 'tests'],
        },
        'test': {
            'type': 'object',
            'properties': {
                'max-diff': {
                    '$ref': '#/definitions/max-diff',
                },
                'parameters': {'type': 'object'},
                'url': {
                    'oneOf': [
                        {'$ref': '#/definitions/simple_var'},
                        {'$ref': '#/definitions/template_var'},
                    ],
                },
                'poll': {
                    'type': 'object',
                    'properties': {
                        'period': {
                            'type': 'integer',
                            'description': 'Poll period in seconds',
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Poll timeout in seconds',
                        },
                    },
                    'required': ['period', 'timeout'],
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
        'max-diff': {
            'type': ['number', 'null'],
            'description': 'Set the case maxDiff option to control error output',  # noqa
        },
    },
}

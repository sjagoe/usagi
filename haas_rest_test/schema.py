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
            }
        },
        'groups': {
            'type': 'array',
            'items': {'$ref': '#/definitions/group'},
        },
    },
    'required': ['version', 'groups'],
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
                'url': {
                    "oneOf": [
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

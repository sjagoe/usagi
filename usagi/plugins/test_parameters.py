# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
import json

from jsonschema.exceptions import ValidationError
from six import BytesIO
import jsonschema
import six
import yaml

from usagi.utils import ExitStack, get_file_path
from ..exceptions import YamlParseError
from .i_test_parameter import ITestParameter


class MethodTestParameter(ITestParameter):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'The HTTP method with which to make a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'method': {
                'enum': ['GET', 'POST', 'DELETE', 'PUT', 'HEAD'],
            },
        },
        'required': ['method'],
    }

    def __init__(self, method):
        super(MethodTestParameter, self).__init__()
        self.method = method
        self.name = 'method'

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(method=data['method'])

    @contextmanager
    def load(self, config):
        yield {self.name: self.method}


class HeadersTestParameter(ITestParameter):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'The HTTP headers to add to a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'headers': {
                'type': 'object',
            },
        },
        'required': ['headers'],
    }

    def __init__(self, headers):
        super(HeadersTestParameter, self).__init__()
        self.headers = headers
        self.name = 'headers'

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(headers=data['headers'])

    @contextmanager
    def load(self, config):
        headers = dict(
            (header_name, config.load_variable(header_name, header_value))
            for header_name, header_value in self.headers.items()
        )
        yield {self.name: headers}


class BodyTestParameter(ITestParameter):

    _format_none = 'none'
    _format_plain = 'plain'
    _format_json = 'json'
    _format_yaml = 'yaml'
    _format_multipart = 'multipart'
    _format_handlers = {
        _format_json: json.dumps,
        _format_yaml: lambda d: yaml.safe_dump(
            d, default_flow_style=False)
    }

    _format_content_types = {
        _format_plain: 'text/plain',
        _format_json: 'application/json',
        _format_yaml: 'application/yaml',
    }

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'A body to send with a request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'body': {
                'type': 'object',
                'properties': {
                    'format': {
                        'enum': [_format_none, _format_plain, _format_json,
                                 _format_yaml, _format_multipart],
                        'default': _format_none,
                    },
                    'lookup-var': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'False to prevent resolving the value as a var.',  # noqa
                    },
                    'value': {
                        'description': 'The value of the body to send.  This will be encoded according to the format',  # noqa
                        'oneOf': [
                            {'$ref': '#/definitions/str'},
                            {'$ref': '#/definitions/obj'},
                        ],
                    },
                },
                'required': ['value'],
            },
        },
        'required': ['body'],
        'definitions': {
            'str': {
                'type': 'string',
            },
            'obj': {
                'type': 'object',
            },
        },
    }

    _format_schemas = {
        _format_multipart: {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'title': 'A multipart/form-data definition',
            'description': 'Test case markup for Haas Rest Test',
            'type': 'object',
            'patternProperties': {
                '^.*$': {
                    'oneOf': [
                        {'$ref': '#/definitions/form-data'},
                        {'$ref': '#/definitions/file'},
                    ],
                },
            },
            'definitions': {
                'str': {
                    'type': 'string',
                },
                'obj': {
                    'type': 'object',
                },
                'form-data': {
                    'description': 'Definition for form fields in a multipart/from-data upload',  # noqa
                    'properties': {
                        'Content-Type': {
                            'type': 'string',
                        },
                        'charset': {
                            'type': 'string',
                            'description': 'Encoding to use for value.  Default UTF-8',  # noqa
                        },
                        'value': {
                            'oneOf': [
                                {'$ref': '#/definitions/obj'},
                                {'$ref': '#/definitions/str'},
                            ],
                        },
                    },
                    'required': ['Content-Type', 'value'],
                },
                'file': {
                    'description': 'Definition for a file field in a multipart/from-data upload',  # noqa
                    'properties': {
                        'filename': {
                            'type': 'string',
                        },
                    },
                    'required': ['filename'],
                },
            },
        },
    }

    def __init__(self, format, lookup_var, value):
        super(BodyTestParameter, self).__init__()
        self._format = format
        self._lookup_var = lookup_var
        self._value = value

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        body = data['body']
        format = body.get('format', cls._format_none)
        value = body['value']

        format_schema = cls._format_schemas.get(format)
        if format_schema is not None:
            try:
                jsonschema.validate(value, format_schema)
            except ValidationError as e:
                raise YamlParseError(str(e))

        return cls(
            format=format,
            lookup_var=body.get('lookup-var', True),
            value=value,
        )

    @property
    def _format_handler(self):
        default = lambda d: d
        return self._format_handlers.get(self._format, default)

    @property
    def _content_type(self):
        return self._format_content_types.get(self._format)

    def _basic_value(self, config):
        value = self._value
        if self._lookup_var:
            value = config.load_variable('value', value)
        return {'data': self._format_handler(value)}

    @contextmanager
    def _multipart_value(self, config):
        is_file = lambda value: 'filename' in value
        file_fields = [(name, value) for name, value in self._value.items()
                       if is_file(value)]
        form_fields = [(name, value) for name, value in self._value.items()
                       if not is_file(value)]

        if self._lookup_var:
            load_variable = lambda n, v: config.load_variable(n, v)
        else:
            load_variable = lambda n, v: v

        fields = {}
        for name, data in form_fields:
            value = load_variable(name, data['value'])
            charset = data.get('charset', 'UTF-8')
            if isinstance(value, six.text_type):
                value = value.encode(charset)

            content_type = '{0}; charset={1}'.format(
                data['Content-Type'], charset)

            fields[name] = ('', BytesIO(value), content_type)

        with ExitStack() as stack:
            for name, data in file_fields:
                file_path = get_file_path(
                    data['filename'], config.test_filename)
                fh = stack.enter_context(open(file_path, 'rb'))
                fields[name] = fh
            yield {'files': fields}

    @contextmanager
    def _get_value(self, config):
        if self._format != self._format_multipart:
            yield self._basic_value(config)
        else:
            with self._multipart_value(config) as value:
                yield value

    @contextmanager
    def load(self, config):
        result = {}

        content_type = self._content_type
        if content_type is not None:
            headers = result['headers'] = {}
            headers['Content-Type'] = content_type

        with self._get_value(config) as value:
            result.update(value)
            yield result


class QueryParamsTestParameter(ITestParameter):

    _schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'The query parameters to attach to a URL for a GET request',
        'description': 'Test case markup for Haas Rest Test',
        'type': 'object',
        'properties': {
            'queryparams': {
                'type': 'object',
                'patternProperties': {
                    '^.*$': {
                        'oneOf': [
                            {'$ref': '#/definitions/boolean'},
                            {'$ref': '#/definitions/number'},
                            {'$ref': '#/definitions/string'},
                        ],
                    },
                },
            },
        },
        'required': ['queryparams'],
        'definitions': {
            'boolean': {'type': 'boolean'},
            'number': {'type': 'number'},
            'string': {'type': 'string'},
        },
    }

    def __init__(self, params):
        super(QueryParamsTestParameter, self).__init__()
        self.params = params
        self.name = 'params'

    @classmethod
    def from_dict(cls, data):
        try:
            jsonschema.validate(data, cls._schema)
        except ValidationError as e:
            raise YamlParseError(str(e))
        return cls(params=data['queryparams'])

    @contextmanager
    def load(self, config):
        yield {self.name: self.params}

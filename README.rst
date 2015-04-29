=====================================
 usagi: Web API test plugin for haas
=====================================

.. image:: https://api.travis-ci.org/sjagoe/usagi.png?branch=master
   :target: https://travis-ci.org/sjagoe/usagi
   :alt: Build status

.. image:: https://coveralls.io/repos/sjagoe/usagi/badge.png?branch=master
   :target: https://coveralls.io/r/sjagoe/usagi?branch=master
   :alt: Coverage status


``usagi`` is a plugin for haas_ that adds support for discovering Web
API test cases descibed in YAML.

``usagi`` requires ``haas v0.6.0`` or later.


.. _haas: https://github.com/sjagoe/haas


Current Features
================

* Describe web API tests using YAML.

* Template URLs to avoid repeating items.

* Variables and target hostname can be provided by environment variables.

* YAML format contains multiple test cases.

* Each test case is a grouping of related tests.

* Make flexible assertions about the server's response.

* Contribute web API test runner functionality through plugins.

* Assert that the SHA256 of the response body matches an expected value.

* Filter JSON response bodies before comparison using ``jq`` filter
  syntax: http://stedolan.github.io/jq/


Plugins
-------

* Var loaders

  * Load from environment

  * Template string based on other vars

  * Load from file, either plaintext or JSON

* Assertions

  * Assert status code

  * Assert header is present or matches value or regexp


TODO
====

* Add more assertions!


Test config format
==================

* ``version``: Currently required, but unverified (we are at
  ``v0.1.0.devN``, after all).

* ``config``: Common test case configuration.

  * ``host``: The name (or IP) of the host to test.

    * Can come from env, template, file, like ``vars``.

  * ``scheme``: The scheme (``http``, ``https``) to use to connect to ``host``

  * ``vars``: Common variable definitions for all test cases; formatted
    as a dictionary of var name to type and value.

    * Simple string vars are allowed.

    * Others are specified as a dictionary with key ``type`` to
      determine how to load.

* ``cases``: Collection of test cases. Each case contains multiple tests

  * ``name``: The name of the test case

  * ``tests``: Collection of individual tests

    * ``name``: The name of the test

    * ``url``: The URI/path relative to ``host`` against which the test
      will be executed.

    * ``method``: The HTTP method to use for the test.

    * ``assertions``: List of assertions to make about the test.


Example Test
------------

.. code-block:: yaml

    ---
      version: '1.0'

      config:
        # Host is loaded as an environment variable
        host:
          type: env
          env: TEST_HOSTNAME
        vars:

          # Simple string var
          api_root: "/api/v1/json"

          # Template var
          metadata:
            type: template
            template: "{api_root}/metadata"

          # Variable loaded as JSON from file
          expected_index:
            type: file
            file: some_file.json
            format: json

      cases:
        - name: "Basic"
          tests:
            - name: "Test root URL"
              url: "/"
              assertions:
                - name: status_code
                  expected: 200
                - name: header
                  header: Content-Type
                  value: text/plain

        - name: "A case"
          tests:
            - name: "Authentication failure"
              url:
                type: template
                template: "{metadata}/auth/required"
              parameters:
                method: GET
                headers:
                  Content-Type: application/json
              assertions:
                - name: status_code
                  expected: 401
                - name: header
                  header: WWW-Authenticate
                  regexp: "Basic realm=.*"
            - name: "POST json"
              url:
                type: template
                template: "{metadata}/post"
              parameters:
                method: POST
                body:
                  format: json
                  lookup-var: false
                  value:
                    some: ["json-compatible", "structure"]
              assertions:
                - name: status_code
                  expected: 204

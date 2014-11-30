============================================
haas-rest-test: Web API test plugin for haas
============================================

.. image:: https://api.travis-ci.org/sjagoe/haas-rest-test.png?branch=master
   :target: https://travis-ci.org/sjagoe/haas-rest-test
   :alt: Build status

.. image:: https://coveralls.io/repos/sjagoe/haas-rest-test/badge.png?branch=master
   :target: https://coveralls.io/r/sjagoe/haas-rest-test?branch=master
   :alt: Coverage status


``haas-rest-test`` is a plugin for haas_ that adds support for
discovering Web API test cases descibed in YAML.

``haas-rest-test`` requires ``haas v0.6.0`` or later.


.. _haas: https://github.com/sjagoe/haas


Example Test
============

.. code-block:: yaml

    ---
      version: '1.0'

      config:
        host:
          type: env
          env: TEST_HOSTNAME
        vars:
          api_root: "/api/v1/json"
          metadata:
            type: template
            template: "{api_root}/metadata"

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
              method: GET
              url:
                type: template
                template: "{metadata}/auth/required"
              assertions:
                - name: status_code
                  expected: 401
                - name: header
                  header: WWW-Authenticate
                  regexp: "Basic realm=.*"


Current Features
================

* Describe web API tests using YAML.

* Template URLs to avoid repeating items.

* Variables and target hostname can be provided by environment variables.

* YAML format contains multiple test cases.

* Each test case is a grouping of related tests.

* Make flexible assertions about the server's response.


TODO
====

* Add more assertions.  Only assertions currently supported are:

  * Status code

  * Headers (string comparison or regexp match)

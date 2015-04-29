=================
 Usagi Changelog
=================

Changes since version 0.2.0
===========================

Enhancements
------------

* Added an assertion type to assert that the sha256sum of a binary
  response matches a provided value (#34).
* Added an option to the body assertion to filter json responses with a
  ``jq`` (https://pypi.python.org/pypi/jq) filter (#44).
* Added an option to cases and tests to allow setting the
  unittest.TestCase.maxDiff parameter (#47).


Version 0.2.0
=============

Enhancements
------------

* Add test option to poll for assertion conditions (#40).


Bug fixes
---------

* Make plaintext body assertions against ``Request.text`` instead of
  invalid ``Request.body`` attribute (#26).


Version 0.1.1 (initial release)
===============================

Features
--------

* A test discovery plugin for ``haas``.

* Generate test cases from YAML.

* Supports plugins for a number of purposes:

  * Provide new methods of loading variables shared between test cases.

  * Provide new methods of creating and passing parameters to ``requests``.

  * Provide new methods of asserting correctness of server responses.

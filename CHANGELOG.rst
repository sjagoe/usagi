=================
 Usagi Changelog
=================

Changes since version 0.1.1
===========================

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

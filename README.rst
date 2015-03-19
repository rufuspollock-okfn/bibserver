BibServer is an open-source RESTful bibliographic data server. BibServer makes
it easy to create and manage collections of bibliographic records such as
reading lists, publication lists and even complete library catalogs.

Main features:

* Create and manage bibliographic collections simply and easily
* Import (and export) your collection from bibtex, MARC, RIS, BibJSON, RDF or
  other bibliogrpaphic formats in a matter of seconds
* Browse collection via an elegant faceted interface
* Embed the collection browser in other websites
* Full RESTful API
* Open-source and free to use


Quick Links
===========

* Code: http://github.com/okfn/bibserver
* Documentation: http://bibserver.readthedocs.org/
* Mailing list: http://lists.okfn.org/mailman/listinfo/openbiblio-dev


Installation
============

See doc/install.rst or
http://bibserver.readthedocs.org/en/latest/install.html


Command Line Usage
==================

Command link script in `cli.py`. To see commands do::

  ./cli.py -h


Developers
==========

To run the tests:

1. Install nose (python-nose)
2. Run the following command::

    nosetests -v test/


Copyright and License
=====================

Copyright 2011-2012 Open Knowledge Foundation.

Licensed under the MIT license



Vendor packages
===============

This BibServer repository also includes the following vendor packages, all of 
which are javascript plugins available under open source license:

* http://jquery.com
* http://jqueryui.com
* http://twitter.github.com/bootstrap
* http://github.com/okfn/facetview
    * http://d3js.org
    * http://code.google.com/p/jquery-linkify/


BibServer_ is a RESTful bibliographic data server.

.. _BibServer: http://bibserver.okfn.org/

Development is taking place in this repo: http://github.com/okfn/bibserver


How It Works
============

Bibliographic files are stored in the BibJSON format - essentially JSON with a
few conventions on what should be used as keys, and where certain types of
information should be stored.

By default, the BibServer code runs a web service just like that available at
http://bibsoup.net. It is possible to take the code and customise to provide
the same functionality under a different brand, or on a local network if
desired.

Records can be uploaded from bibTex, BibJSON, or CSV files, and will
automatically generate a collection that can be browsed via the web site. Also,
additional parsers can easily be written and used in your local version, or
submitted for inclusion to the BibServer repository so others can use them too.

Collections can be browsed via the online service, and content negotiation can
be performed to receive an HTML or JSON output. The search functionality
utilises an underlying SOLR (moving to ES soon) index, and can be directly
queried for responses.

BibServer uses code from some other projects (facetview and solreyes), but for
ease of installation these have all been included in this repo. We have plans
to develop further functionality, including being able to parse more source
formats; installation information and development plans are being detailed on
our web site at http://bibserver.okfn.org.


Install
=======

1. Install pre-requisites:
   
   * Python, pip and virtualenv.
   * ElasticSearch_ (0.17 series)

2. [optional] Create a virtualenv and enable it::

    # in bash
    virtualenv {myenv}
    . {myenv}/bin/activate

3. Get the source::

    # by convention we put it in the virtualenv but you can put anywhere
    mkdir {myenv}/src
    git clone https://github.com/okfn/bibserver {myenv}/src/

3. Install the app::

    # install other python modules
    pip install pyes

    # now BibServer
    # go to wherevevr you have the bibserver file, and enter it
    cd {myenv}/src/bibserver
    # do a development install from current directory
    pip install -e .
    # alternatively if you do not want a development install you could just do
    # python setup.py install

4. Run the webserver::

    # in the bibserver folder:
    # don't worry, there is a bibserver subdirectory in bibserver, so this should run fine.
    python bibserver/web.py

.. _ElasticSearch: http://www.elasticsearch.org/


Command Line Usage
~~~~~~~~~~~~~~~~~~

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

Copyright 2011 Open Knowledge Foundation.

Licensed under the `GNU Affero GPL v3`_

.. _GNU Affero GPL v3: http://www.gnu.org/licenses/agpl.html


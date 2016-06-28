============
Installation
============

Simple Setup
============

1. Install pre-requisites:
   
   * Python (>= 2.7), pip and virtualenv.
   * git
   * ElasticSearch_ (> 0.17 series)

2. [optional] Create a virtualenv and enable it::

    # in bash
    virtualenv {myenv}
    . {myenv}/bin/activate

3. Get the source::

    # by convention we put it in the virtualenv but you can put anywhere
    # mkdir {myenv}/src
    # git clone https://github.com/okfn/bibserver {myenv}/src/
    git clone https://github.com/okfn/bibserver

3. Install the app::

    # move to your checkout of bibserver
    # cd {myenv}/src/bibserver
    cd bibserver
    # do a development install from current directory
    pip install -e .
    # alternatively if you do not want a development install
    # note there is an error with this at the moment - do dev install
    # python setup.py install

4. Run the webserver::

    python bibserver/web.py

.. _ElasticSearch: http://www.elasticsearch.org/


See doc/deploy.rst or https://bibserver.readthedocs.io/en/latest/deploy.html
for more details on a full installation


Install example
===============

Install commands on a clean installation of Ubuntu_11.10_::

    sudo apt-get install python-pip python-dev build-essential 
    sudo pip install --upgrade pip 
    sudo pip install --upgrade virtualenv 
    sudo apt-get install git

    wget https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.18.2.tar.gz
    tar -xzvf elasticsearch-0.18.2.tar.gz
    ./elasticsearch-0.18.2/bin/elasticsearch start

    virtualenv .
    . ./bin/activate
    
    git clone https://github.com/okfn/bibserver
    cd bibserver
    pip install -e .
    
    python bibserver/web.py
    
You will now find your bibserver running at localhost:5000.
    
.. _Ubuntu_11.10: http:ubuntu.com



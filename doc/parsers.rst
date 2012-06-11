.. _parsers:

===============
Parsing sources
===============

It is possible to run the ingest tools separately - enabling processing of 
biblio records from multiple formats into bibJSON.


Import via Bibserver
====================

The most common way of importing bibliographic records into Bibserver is using the Upload form in the web interface.
See :ref:`upload`.

Detail this, including explanation of importer.py


Stand-alone parsing
===================

Detail how to run stand-alone, and explain workings of ingest.py


The parsers
===========

For each kind of file that can be imported into a Bibserver, a 'parser' exists.
A parser is an executable file that accepts a file format on standard input and always outputs Bibjson.
The parsers are stored in a directory called 'parserscrapers_plugins' by default.

When the importing subsystem of Bibserver (named 'ingest') is initialised, all the executable files
found in the parserscrapers_plugins directory are executed with a -bibserver command line parameter.
A parser _must_ recognise this parameter and output a JSON config section in response, indicating if this is a  valid Bibserver parser and the format that is supported.
All the parsers found are stored in a json data snippet named 'plugins.json' which can be used to determine what the current list of supported data formats for a given instance are. (this is used for example in the Upload forms)

The download cache
==================

When a data import is submitted to Bibserver, a 'ticket' is made which tracks the progress of the upload.
The ticket lists the format of the imported data, who requested it, the time it was made and the progress of the import. When an import is completed, it is also possible to see the raw data, plus the resulting Bibjson data.

The ingest tickets, downloaded data plus resulting Bibjson are all stored in a directory named 'download_cache' by default. (this location can be changed in the config.json file)
The list of tickets in a system can be viewed on the /ticket/ URL. Each ticket has an ID, and one could then view either the source data /ticket/<ticket id>/data or the resulting Bibjson /ticket/<ticket id>/bibjson

All the data in a Bibserver instance can be listed by looking at a URL: /data.txt. This produces a text file with the URL for each Bibjson data file per line. This can be used for automated buld data downloads of Bibserver data.

Making a new parser
===================

Even though Bibserver is written in Python, it is not necessary to write a parser in Python - it can be written in any programming language. At the time of writing there is one example parser written in Perl to support the MARC format, which is commonly found in library automation systems.

To make a new parser:

- you should be able to make standalone executable in the parserscrapers_plugins that can be called from a shell

- the parser must support the -bibserver command line paramater which gives details about the data format supported

- read data from standard input, parse and convert the data to Bibjson, and print the resulting Bibjson to standard output.

TODO: Explain how to make a new parser, and how to submit a pull request or email to 
include it in the repo.

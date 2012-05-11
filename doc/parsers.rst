===============
Parsing sources
===============

It is possible to run the ingest tools separately - enabling processing of 
biblio records from multiple formats into bibJSON.


Import via Bibserver
====================

Detail this, including explanation of importer.py


Stand-alone parsing
===================

Detail how to run stand-alone, and explain workings of ingest.py


The parsers
===========

Explain a bit about the current parsers, how they register their availability
and get called by ingest.


The download cache
==================

Explain about the local copy, how they can be accessed, how the raw bibjson can 
be accessed after conversion.


Making a new parser
===================

Explain how to make a new parser, and how to submit a pull request or email to 
include it in the repo.

Use python one as default, but note that they do not have to be python - example 
the MARC parser in perl.



.. _upload:

=====================
Uploading collections
=====================

When a bibserver instance is configured to allow uploads, it is possible to 
upload from a source URL or file from PC into the instance via the /upload page.

A typical bibserver will support upload from the parsers it has available to it 
- read more about the parsers and running them independently, or writing new ones, 
on the parsers documentation page - :ref:`parsers`


The upload page
===============

To upload, just go to the upload page. Provide a URL or file, a collection name 
and description, confirm the license and the format type.

The Upload form can either be given a URL from which the Bibserver will retrieve the data to import, or a user can upload a file from her local machine to be imported. Bibserver tries to guess the format of the supplied URL by looking at the filename extension of the supplied URL. (this is unreliable and might be removed in future).
If the fileformat can not be guessed, a list of supported fileformats for that install of Bibserver is shown.

If a converter of the right format is not available, your source file can be 
converted elsewhere into JSON following the bibJSON standard, then the JSON 
file can be imported directly.


Upload from other online services
=================================

Examples of providing URLs for uploading directly from other online sources 
such as bibsonomy.


Monitoring tickets
==================

Explain the tickets page, and the info that can be got there.


Viewing an uploaded collection
==============================

On upload, a tidy version of collection name is made for URL.

Once a collection has uploaded, it can be found at /username/collection.



Multiple files to same collection
=================================

Confirm what happens when uploading mutliple files of different content to the
same collection name


Overwriting records and internal IDs
====================================

Mention the method by which internal IDs are allocated, and how records can be 
overwritten if an upload is performed of records that are somewhat identical to 
current records. Point out what this means for local edits.



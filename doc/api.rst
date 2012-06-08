===========
The web API
===========


web.py and search.py
====================

Detail the workings of the web.py file.

Explain the search.py file too, which is used by web.py extensively.


URL routes
==========

/
-

methods GET

returns HTML

The front page of the web service.

/faq
----

methods GET

returns HTML

The frequently asked questions page of the web service.

/account
--------

* /account/register
* /account/login
* /account/logout

returns HTML

Esed for account creation via a web browser, although it would be
possible to register a new account by POSTing to the registration endpoint.


/query
------

* /query/record
* /query/collection

methods GET or POST

returns JSON

Exposes the query endpoints of the elasticsearch backend indices, so 
queries can be issued against it directly. 

For exmaple /query/record/_search?q=* will return all records in the standard 
ten results at a time.

/users
------

requires authorisation

methods GET

returns HTML or JSON

Provides a list of users

/collections
------------

* /collections/<username>/<collection>

methods GET

returns HTML or JSON

Provides a list of collections

/upload
-------

methods GET (to return the browser form) or POST

requires authorisation

LIST THE PARAMS

For uploading from source files into collections.

/create
-------

not implemented

For creating new records.

/<username>
-----------

* /<username>/<collection>
* /<username>/<collection>/<record>

methods GET or POST or DELETE

returns HTML or JSON

requires authorisation for retrieval of user data via GET, and for POSTs

Access information about a user, a collection, or a record. Also update the 
records by POSTing updated versions.

/<implicitfacet>/<implicitvalue>
--------------------------------

methods GET

returns HTML or JSON

Anything that is not matched to a known endpoint but that can be matched to a 
key in the record index will cause an attempt to interpret it as an implicit 
value. For example, /year/2012 will attempt to return all records in the index 
(therefore across all collections) that have a a key called "year" where the 
value equals "2012".

/search
-------

methods GET

returns HTML or JSON

The search endpoint allows for search across the full record index of the instance.

/<anything>
-----------

Any route that cannot be matched to any previous endpoint, including an implicit
facet, performs the same as the /search endpoint.


Programmatic access
===================

The API endpoints can be queried either via a web browser - which defaults to 
providing HTML output, of course - or programmatically by requests e.g. via cURL.

Requests for access to data operate as usual - but requests to insert data 
require authentication; this is achieved via API keys. Every user account has 
an API key assigned to it, which can be retrieved from the /username page; it 
can then be provided as a parameter to any request that attempts to submit data
into the system - e.g. a request to the /upload endpoint.

Each endpoint can return HTML or JSON; JSON can be requested either by appending 
.json to the URL portion, or adding format=json to the URL parameters, or by 
setting the "accept" headers on your request to "application/json".

Here is an example of retrieving some records from a collection via cURL:

ADD EXAMPLE

Here is an example of submitting a new collection via cURL:

ADD EXAMPLE





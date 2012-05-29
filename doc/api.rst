===========
The web API
===========


URL routes
==========

/

/account
/account/register
/account/login
/account/logout

/query
/query/

/users

/collections

/upload    

/create - not implemented yet

/username
/username/collection
/username/collection/record

/implicitfacet/facetvalue

/search

/anythingelse - defaults to a search


web.py and search.py
====================

Detail the workings of the web.py file.

Explain the search.py file too, which is used by web.py extensively.


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





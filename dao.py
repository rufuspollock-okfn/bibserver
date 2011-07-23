import json

# this is the dao layer
# what it does depends on what the storage layer is

class dao(object):

    # given a collection as python list of bibjson
    def save(self,data):
        # need to do checks to see if this collection already exists
        # perhaps by source URL
        
        # save to couchdb
        if False:
            import couchdb
            couch = couchdb.Server(url='http://localhost:5984')
            db = couch['bibsoup']
            for item in data:
                db.save(item)
        
        # save to solr
        if True:
            from solrindexer import SolrIndexer
            i = SolrIndexer()
            i.index(data)

        # save to elasticsearch
        if False:
            pass



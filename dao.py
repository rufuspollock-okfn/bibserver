# this is the data access layer
# what it does depends on what the storage layer is

import json
import httplib

class dao(object):

    def __init__(self):
        self.saveto = ["solr"]
        self.index = "solr"
        self.couchdb_dbname = "bibsoup"
        self.couchdb_url = "http://localhost:5984"
        self.solr_url = "localhost:8983"
        self.solr_update_path = "/solr/update/json?commit=true"
        self.solr_query_path = "/solr/select"
        self.es_url = "localhost:9200"
        self.es_path = "/bibsoup/record/_search"

    # get data from index
    def query(self,get="",data=""):
        self.get = get
        self.data = data
        self.url = ""
        self.path = ""
        if self.index == "solr":
            self.url = self.solr_url
            self.path = self.solr_query_path + get
        if self.index == "es":
            self.url = self.es_url
            self.path = self.es_path + get
        c =  httplib.HTTPConnection(self.url)
        if self.data != "":
            c.request('POST', self.path, self.data)
        else:
            if self.get == "":
                return "query endpoint. please provide query parameters. index type is " + self.index + ", standard query syntax and methods apply"
            c.request('GET', self.path)
        result = c.getresponse()
        #print self.index, self.url, self.path, result.status, result.reason
        return result.read()

    # given a collection as python list of bibjson
    # add user auth to this if necessary
    def save(self,data):
        # need to do checks to see if this collection already exists
        # perhaps by source URL
        
        # save to couchdb
        if "couchdb" in self.saveto:
            import couchdb
            couch = couchdb.Server(url=self.couchdb_url)
            db = couch[self.couchdb_dbname]
            for row in data:
                db.save(row)
        
        # save to solr
        # ensure SOLR is configured to accept JSON
        # <requestHandler name="/update/json" class="solr.JsonUpdateRequestHandler"/>
        # as per: http://wiki.apache.org/solr/UpdateJSON
        if "solr" in self.saveto:
            for row in data:
                insert = '{"add":{"doc":' + json.dumps(row) + '}}'
                c =  httplib.HTTPConnection(self.solr_url)
                #c.request('POST', self.solr_update_path, insert)
                #result = c.getresponse()
                print insert #result.status, result.reason

        # save to elasticsearch
        if "es" in self.saveto:
            for row in data:
                pass

    # do deletions
    def delete(self):
        pass

    # do updates
    def update(self):
        pass

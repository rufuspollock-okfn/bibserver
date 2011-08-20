# this is the data access layer
import json
import httplib
import pyes

from bibserver.config import config

def init_db():
    conn, db = get_conn()
    try:
        conn.create_index(db)
    except pyes.exceptions.IndexAlreadyExistsException:
        pass

def get_conn():
    host = str(config['ELASTIC_SEARCH_HOST'])
    db_name = config['ELASTIC_SEARCH_DB']
    conn = pyes.ES([host])
    return conn, db_name


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

    # get record from the index
    def record(self,rid):
        if self.index == "solr":
            res = json.loads( self.query('?wt=json&q=_id:' + rid) )
            if len(res["response"]["docs"]) == 0:
                return {"error":"no match"}
            if len(res["response"]["docs"]) > 1:
                return {"error":"multiple match"}
            return res["response"]["docs"][0]
        if self.index == "es":
            res = json.loads( self.query('?q=_id:' + rid) )
            if len(res["hits"]["hits"]) == 0:
                return {"error":"no match"}
            if len(res["hits"]["hits"]) > 1:
                return {"error":"multiple match"}
            return res["hits"]["hits"][0]["_source"]


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
                insert = '{"add":{"doc":' + json.dumps(row,encoding="8859") + '}}'
                c =  httplib.HTTPConnection(self.solr_url)
                c.request('POST', self.solr_update_path, insert)
                result = c.getresponse()
                #print insert, result.status, result.reason

        # save to elasticsearch
        if "es" in self.saveto:
            for row in data:
                pass

    # do deletions
    # however, should never delete. just update and remove from collection
    # so delete is actually only a super admin function
    # ha ha, ATR
    def delete(self,rid):
        pass

    # do updates
    def update(self):
        pass

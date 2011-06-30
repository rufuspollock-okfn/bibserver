from serialisers.SolrSerialiser import SolrSerialiser
import httplib2

class Indexer(object):

    def __init__(self, solr_url=None):
        self.solr_url = solr_url if solr_url is not None else "http://localhost:8983/solr/update"

    def index(self, bibdataset):
        solr = SolrSerialiser()
        xml = solr.serialise(bibdataset)
        self.post(xml)

    def post(self, data):
        h = httplib2.Http()
        h.request(self.solr_url + "?commit=true", method="POST", body=data)

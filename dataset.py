# convert a source file to bibjson

"""
from datasource import DataSource
ds = DataSource()
d = ds.import_from("http://bibserver.berkeley.edu/DB/UCB_MATH1/Arveson__William_B.bib")
from serialisers.JsonSerialiser import JsonSerialiser
s = JsonSerialiser()
j = s.serialise(d)

from datasource import DataSource
ds = DataSource()
d = ds.import_from("http://bibserver.berkeley.edu/DB/UCB_MATH1/Arveson__William_B.bib")
from serialisers.SolrSerialiser import SolrSerialiser
solr = SolrSerialiser()
xml = solr.serialise(d)

from datasource import DataSource
ds = DataSource()
d = ds.import_from("http://bibserver.berkeley.edu/DB/UCB_MATH1/Arveson__William_B.bib")
from indexer import Indexer
i = Indexer()
i.index(d)

curl -X POST -H "Content-Type: text/xml" --data "<delete><query>collection:aldous</query></delete>" http://localhost:8983/solr/update?commit=true
"""

import urllib2
import json
from parsers.BibTexParser import BibTexParser

class DataSet(object):
    
    def convert(self, url, format):
        source = urllib2.urlopen(url)
        data = source.read()
        if format == "bibtex":
            parser = BibTexParser()
            d = parser.parse(data)
        if format == "bibjson":
            d = data
        # write data to file (maybe just for testing)
        tidyname = url.replace("/","___")
        fh = open('store/bibjson/' + tidyname, 'w')
        fh.write( json.dumps(d) )
        fh.close()
        
        return d

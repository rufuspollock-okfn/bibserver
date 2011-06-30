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

curl -X POST -H "Content-Type: text/xml" --data "<delete><query>*:*</query></delete>" http://localhost:8983/solr/update?commit=true
"""

import urllib2
from parsers.BibTexParser import BibTexParser
from model import BibliographicDataSet

class DataSource(object):
    
    def import_from(self, url):
        source = urllib2.urlopen(url)
        data = source.read()
        parser = BibTexParser()
        d = parser.parse(data)
        return BibliographicDataSet(d)

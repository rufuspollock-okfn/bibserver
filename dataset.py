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
import csv
import json
from parsers.BibTexParser import BibTexParser

class DataSet(object):
    
    def convert(self, package):
        self.localfile = package["localfile"]
        self.url = package["source"]
        self.format = package["format"]
        
        fh = open('store/raw/' + self.localfile, 'r')
        
        # read source and convert
        if self.format == "bibtex":
            d = fh.read()
            parser = BibTexParser()
            data = parser.parse(d)
        if self.format == "bibjson":
            data = fh.read()
        if self.format == "csv" or self.format == "google":
            # convert from csv to json
            data = csv.dictReader( fh )
            #data = {}
            #for k,v in d:
            #    data(k) = v
            #pass
        
        fh.close()
        
        # add collection information
        data = self.prepare_collection(data,package)
        
        # write data to file (maybe just for testing)
        tidyname = self.url.replace("/","___")
        fh = open('store/bibjson/' + tidyname, 'w')
        fh.write( json.dumps(data) )
        fh.close()
        
        return data
    
    # set the collection metadata
    def prepare_collection(self,data,package):
        jsonObj = []
        
        has_meta = False
        meta = None
        
        source = package["source"]
        collection = package["collection"]
        
        for record in data:
            if record.get('bibtype') == "comment" and not has_meta:
                meta = self.get_meta(record)
                if "source" not in meta:
                    meta['source'] = source
                if "collection" not in meta:
                    meta['collection'] = collection
                else:
                    collection = meta["collection"]
                has_meta = True
            else:
                bibjson = record
                if "collection" not in bibjson:
                    bibjson['collection'] = collection
                # parse people out of the record
                bibjson = parse_people(bibjson)
                jsonObj.append(bibjson)
        
        if meta is not None:
            jsonObj = [meta] + jsonObj
        
        return jsonObj

    # used by set_colllection to find meta record
    def get_meta(self, record):
        meta = {}
        meta["class"] = "metadata"
        for k, v in record.iteritems():
            meta[k.lower()] = v
        return meta
    
    # parse potential people names out of a collection file
    # check if they have a person record in bibsoup
    # if not create one
    # append person IDs to a person attribute of every record
    def parse_people(self,record):
        if "person" in record:
            return record

        record["person"] = []
        if "author" in record:
            for author in record["author"]:
                person = self.do_person(author)
                if person not in record["person"]:
                    record["person"].append( person )
        if "advisor" in record:
            for advisor in record["advisor"]:
                person = self.do_person(advisor)
                if person not in record["person"]:
                    record["person"].append( person )
    
    # find the person in the index and return their ID
    # or create a new one and return the new ID
    def do_person(self,person):
        return person
                    











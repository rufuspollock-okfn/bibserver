# convert a source file to bibjson

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
            data = parser.parse(d,package)
        if self.format == "bibjson":
            data = fh.read()
        if self.format == "csv" or self.format == "google":
            data = csv.dictReader( fh )
            #data = {}
            #for k,v in d:
            #    data(k) = v
            #pass
        
        fh.close()
        
        # parse people out of the data
#        self.parse_people(data)
        
        
        return data
    
    
    # parse potential people names out of a collection file
    # check if they have a person record in bibsoup
    # if not create one
    # append person IDs to a person attribute of every record
    def parse_people(self,data):
        for record in data:
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
    # on new creation, write a file to the store too
    def do_person(self,person):
        return person
                    











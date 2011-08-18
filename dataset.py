# convert a source file to bibjson

import urllib2
import uuid
import csv
import json
from parsers.BibTexParser import BibTexParser

class DataSet(object):
    
    def convert(self, package):
        self.localfile = package["localfile"]
        self.format = package["format"]
        
        fh = open('store/raw/' + self.localfile, 'r')
        
        # read source and convert
        if self.format == "bibtex":
            d = fh.read()
            parser = BibTexParser()
            data = parser.parse(d)
        if self.format == "bibjson":
            data = json.loads( fh.read() )
        if self.format == "csv" or self.format == "google":
            d = csv.DictReader( fh )
            data = []
            # do any required conversions
            for row in d:
                print row
                if "author" in row:
                    row["author"] = row["author"].split(",")
                data.append(row)
        
        fh.close()
        
        # parse people out of the data
#        self.parse_people(data)
        
        data = self.prepare(data,package)
        
        return data
    
    
    # check prepare the data in various ways
    def prepare(self,data,pkg):
        for index,item in enumerate(data):
            # if collection name provided, check it is in each record, or add it if not
            if pkg["collection"] != "":
                data[index]["collection"] = [pkg["collection"]]

            # give item a uuid
            if "_id" not in item:
                data[index]["_id"] = str( uuid.uuid4() )

            # if people names are provided, e.g. in author fields, check for person records for them
            # if not existing, create one.
            # append person record details to records

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
                    











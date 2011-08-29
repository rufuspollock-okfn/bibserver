# convert a source file to bibjson

import urllib2
import uuid

from parsers.BibTexParser import BibTexParser
from parsers.JSONParser import JSONParser
from parsers.CSVParser import CSVParser

class DataSet(object):
    
    def convert(self, fileobj, format, collection=None):
        '''Convert a source datastream in fileobj in `format` (e.g. bibtex) to
        bibjson and add it to `collection`.

        :return: a python dict json-i-fiable to bibjson.
        '''
        if format == "bibtex":
            d = fileobj.read()
            parser = BibTexParser()
            data = parser.parse(d)
        elif format == "bibjson":
            parser = JSONParser()
            data = parser.parse(fileobj)
        elif format == "csv" or format == "google":
            parser = CSVParser()
            data = parser.parse(fileobj)
        else:
            raise Exception('Unable to convert from format: %s' % format)

        data = self.prepare(data, collection)
        return data
    
    
    # prepare the data in various ways
    def prepare(self,data, collection=None):
        for index,item in enumerate(data):
            # if collection name provided, check it is in each record, or add it if not
            if collection:
                data[index]["collection"] = collection

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
                    











# the data import manager
# gets an uploaded file or retrieves a file from a URL
# Uses the parser manager to parse the file
# indexes the records found in the file by upserting via the DAO

import urllib2
import re
from cStringIO import StringIO

from bibserver.parser import Parser
import bibserver.dao

class Importer(object):
    def upload(self, pkg):
        '''upload content and index it'''
        
        if "upfile" in pkg:
            pkg["fileobj"] = pkg["upfile"]
        elif "data" in pkg:
            pkg["fileobj"] = StringIO(pkg['data'])
        elif "source" in pkg:
            pkg["fileobj"] = urllib2.urlopen( pkg["source"] )
        
        # look for a collection like this already existing
        # if the source location is the same, delete and reupload
        # if not the same, refuse
        # if a file upload as opposed to URL provision, check email addr?
        
        return self.index(pkg)

    
    def bulk_upload(self, colls_list):
        '''upload a list of collections from provided file locations
        colls_list looks like the pkg.
        So should have source for a URL, or upfile for a local file
        {
            collections: [
                {
                    source: "sample.bibtex",
                    format: "bibtex",
                    collection: "coll1"
                },
                ...
            ]
        }
        '''
        try:
            for coll in colls_list["collections"]:
                self.upload(coll)
            return True
        except:
            return False
    
    
    # index the content
    def index(self, pkg):
        '''index a file'''
        parser = Parser()
        data = parser.parse(pkg["fileobj"], pkg["format"])

        # prepare the data as required
        data = self.prepare(data,pkg)
        
        # send the data list for bulk upsert
        return bibserver.dao.Record.bulk_upsert(data)


    # prepare the data in various ways
    def prepare(self,data,pkg):
        for index,item in enumerate(data):
            
            # strip the bibtex record for now
            if data[index]["bibtex"]:
                del data[index]["bibtex"]
            
            # if collection name provided, check it is in each record, or add it if not
            if "collection" in pkg:
                if "collection" in data[index]:
                    if isinstance('List',data[index]["collection"]):
                        data[index]["collection"] = data[index]["collection"].append(pkg["collection"])
                    elif isinstance('String',data[index]["collection"]):
                        data[index]["collection"] = [data[index]["collection"],pkg["collection"]]
                    else:
                        data[index]["collection"] = pkg["collection"]
                else:
                    data[index]["collection"] = pkg["collection"]
            else:
                # if no package collection name, read it out of the provided records
                if "collection" in data[index]:
                    pkg["collection"] = data[index]["collection"]

        # add the package info to the collection
        pkg["type"] = "bibserver_pkg_metadata"
        if "data" in pkg:
            del pkg["data"]
        if "fileobj" in pkg:
            del pkg["fileobj"]
        if "upfile" in pkg:
            del pkg["upfile"]
        data.insert(0,pkg)
        
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
                    






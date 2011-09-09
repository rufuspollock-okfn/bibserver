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

        return self.index(pkg)

    
    def bulk_upload(self, colls_list):
        '''upload a list of collections from provided file locations
        colls_list looks like the pkg, so should have source for a URL, 
        or upfile for a local file'''
#        try:
        for coll in colls_list["collections"]:
            self.upload(coll)
        return True
#        except:
#            return False
    
    
    # index the content
    def index(self, pkg):
        '''index a file'''
        parser = Parser()
        data = parser.parse(pkg["fileobj"], pkg["format"])

        # prepare the data as required
        data, pkg = self.prepare(data,pkg)
        
        # if allowed to index, then index (match source or email)
        if self.can_index(pkg):
            if "collection" in pkg:
                bibserver.dao.Record.delete_by_query("collection:" + pkg["collection"])
            # send the data list for bulk upsert
            return bibserver.dao.Record.bulk_upsert(data)
        else:
            return "DUPLICATE"


    def can_index(self,pkg):
        '''check if a pre-existing collection of same name exists.
        If so, only allow re-index if either source or email match.
        '''
        try:
            res = bibserver.dao.Record.query(q='collection:' + pkg["collection"] + ' AND type:collection')
            if "source" in res["hits"]["hits"][0]["_source"]:
                if pkg["source"] == res["hits"]["hits"][0]["_source"]["source"]:
                    return True
                else:
                    return False
            elif "email" in res["hits"]["hits"][0]["_source"]:
                if pkg["email"] == res["hits"]["hits"][0]["_source"]["email"]:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return True


    # prepare the data in various ways
    def prepare(self,data,pkg):
    
        # replace white space in collection name with _
        if "collection" in pkg:
            pkg["collection"] = pkg["collection"].replace(" ","_")
    
        # if no collection name provided, build a collection name if possible
        if "collection" not in pkg:
            # build collection name from source URL
            if "source" in pkg:
                derived_name = pkg["source"].replace("http://","").replace("https://","").replace("/","").replace(".","").replace("~","")
                pkg["collection"] = derived_name

            # build collection name from source URL
            elif "email" in pkg and pkg["email"] is not None:
                derived_name = pkg["email"].replace("@","").replace(".","")
                pkg["collection"] = derived_name

        
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
                # if no package collection name, try to find one in the provided records
                if "collection" in data[index]:
                    pkg["collection"] = data[index]["collection"]

        # add the package info to the collection
        pkg["type"] = "collection"
        metadata = pkg
        if "data" in metadata:
            del metadata["data"]
        if "fileobj" in metadata:
            del metadata["fileobj"]
        if "upfile" in metadata:
            del metadata["upfile"]
        data.insert(0,metadata)
        
        return data, pkg


    # THE FOLLOWING ARE NOT USED

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
                    






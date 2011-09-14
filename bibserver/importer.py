# the data import manager
# gets an uploaded file or retrieves a file from a URL
# Uses the parser manager to parse the file
# indexes the records found in the file by upserting via the DAO

import urllib2
import re
from cStringIO import StringIO
import unicodedata

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
                #derived_name = pkg["source"].replace("http://","").replace("https://","").replace("/","").replace(".","").replace("~","")
                #pkg["collection"] = derived_name
                pkg["collection"] = pkg["source"]

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
            
            # look for people records
            data[index] = self.parse_people(data[index])

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


    # parse potential people out of a record
    # check if they have a person record in bibsoup
    # if not create one
    # append person IDs to a person attribute of every record
    def parse_people(self,record):
        if "person" not in record:
            record["person"] = []
        if "author" in record:
            record["person"].extend(self.do_people(record["author"]))
        if "advisor" in record:
            record["person"].extend(self.do_people(record["advisor"]))
        if "editor" in record:
            record["person"].extend(self.do_people(record["editor"]))
        return record
    
    def do_people(self,people):
        persons = []
        if isinstance(people,str):
            persons = self.do_person(people)
        if isinstance(people,list):
            for person in people:
                persons.append(self.do_person(person))
        return persons
    
    def do_person(self,person_string):
        results = bibserver.dao.Record.query(q='type.exact:"person" AND alias.exact:"' + person_string + '"')
        if results["hits"]["total"] != 0:
            return results["hits"]["hits"][0]["_source"]["person"]

        looseresults = bibserver.dao.Record.query(q='type.exact:"person" AND "*' + person_string + '*"',flt=True,fields=["person"])
        if looseresults["hits"]["total"] != 0:
            tid = looseresults["hits"]["hits"][0]["_id"]
            data = bibserver.dao.Record.get(tid)
            if person_string not in data["alias"]:
                data["alias"].append(person_string)
            # pyes does not seem to be accepting updates - I could be doing it wrong...
            #bibserver.dao.Record.upsert(data)
            import httplib
            import json
            host = "127.0.0.1:9200"
            db_name = "bibserver"
            fullpath = '/' + db_name + '/record/' + tid
            c =  httplib.HTTPConnection(host)
            c.request('PUT', fullpath, json.dumps(data))
            c.getresponse()

            return data["person"]

        ident = person_string.replace(" ","").replace(",","").replace(".","")
        data = {"person":ident,"type":"person","alias":[person_string]}
        bibserver.dao.Record.upsert(data)
        return ident



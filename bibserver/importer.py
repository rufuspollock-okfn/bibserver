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
            fileobj = pkg["upfile"]
        elif "data" in pkg:
            fileobj = StringIO(pkg['data'])
        elif "source" in pkg:
            fileobj = urllib2.urlopen( pkg["source"] )
        
        created_records = self.index(fileobj, pkg["format"], pkg.get("collection",None))

        return created_records
    
    def bulk_upload(self, colls_list):
        '''upload a list of collections from provided file locations
        colls_list looks like
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

        for coll in colls_list["collections"]:
            self.upload(coll)
    
    
    # index the content
    def index(self, fileobj, format, collection=None):
        '''index a file'''
        parser = Parser()
        data = parser.parse(fileobj, format, collection)
        # send the data list for bulk upsert
        result = bibserver.dao.Record.bulk_upsert(data)
        return result


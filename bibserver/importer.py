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
            fileobj = self.retrieve(pkg)
        created_records = self.index(fileobj, pkg)

        return created_records
    

    # retrieve from URL into store
    def retrieve(self,pkg):
        url = pkg["source"]
        # grab a google spreadsheet as csv
        # https://spreadsheets.google.com/spreadsheet/ccc?key=0AnCtSdb7ZFJ3dEEzWmR4QzM5YW5OYlVHdV81UW90cXc&hl=en_GB
        if pkg["format"] == "google":
            key = re.sub(r'.*key=',"",url)
            key2 = re.sub(r'&.*',"",key)
            url = "http://spreadsheets.google.com/tq?tqx=out:csv&tq=select *&key=" + key2
        content = urllib2.urlopen( url )
        return content
    
    # index the content
    def index(self, fileobj, pkg):
        '''index a file in the store'''
        parser = Parser()
        collection = pkg.get('collection', None)
        data = parser.parse(fileobj, pkg['format'], collection)
        # send the data list for bulk upsert
        result = bibserver.dao.Record.bulk_upsert(data)
        return result


# the new data upload manager

import urllib2
import json
import re
import os
import datetime
from cStringIO import StringIO

from dataset import DataSet
import bibserver.dao

class Manager(object):
    def schedule(self, pkg):
        '''schedule something to be imported.

        For now, does not schedule. just executes.
        '''
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
    
    def index(self, fileobj, pkg):
        '''index a file in the store'''
        ds = DataSet()
        collection = pkg.get('collection', None)
        data = ds.convert(fileobj, pkg['format'], collection)
        for record in data:
            bibserver.dao.Record.upsert(record)
        return data


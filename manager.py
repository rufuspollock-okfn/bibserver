# the new data upload manager

import urllib2
import json
import re

from dataset import DataSet
from dao import dao

class Manager(object):

    # schedule something
    # for now, does not schedule. just executes.
    def schedule(self,pkg):
        if "upfile" in pkg or "data" in pkg:
            pkg["localfile"] = self.store(pkg)
        if "source" in pkg:
            pkg["localfile"] = self.retrieve(pkg)
        self.index(pkg)
    
    # retrieve from URL into store
    def retrieve(self,pkg):
        # add in checks to see if current local copy is same as remote copy
        url = pkg["source"]

        # grab a google spreadsheet as csv
#https://spreadsheets.google.com/spreadsheet/ccc?key=0AnCtSdb7ZFJ3dEEzWmR4QzM5YW5OYlVHdV81UW90cXc&hl=en_GB
        if pkg["format"] == "google":
            key = re.sub(r'.*key=',"",url)
            key2 = re.sub(r'&.*',"",key)
            url = "http://spreadsheets.google.com/tq?tqx=out:csv&tq=select *&key=" + key2

        content = urllib2.urlopen( url )
        tidyname = url.replace("/","___")
        fh = open('store/raw/' + tidyname, 'w')
        fh.write( content.read() )
        fh.close()
        return tidyname
    
    # store uploaded file
    def store(self,pkg):
        if "upfile" in pkg:
            uploadfile = pkg["upfile"]
            filepath = uploadfile.upfile.filename.replace('\\','/')
            filename = pkg["ip"] + "_" + pkg["received"] + "_" + filepath.split('/')[-1]
            fh = open('store/raw/' + filename, 'w')
            fh.write( uploadfile.upfile.file.read() )
            fh.close()
        if "data" in pkg:
            filename = "POST_" + pkg["ip"] + "_" + pkg["received"]
            fh = open('store/raw/' + filename, 'w')
            fh.write( pkg["data"] )
            fh.close()            
        return filename

    
    # index a file in the store
    def index(self,pkg):
        ds = DataSet()
        data = ds.convert(pkg)

        # write data to file (maybe just for testing)
        fh = open('store/bibjson/' + pkg["localfile"], 'w')
        fh.write( json.dumps(data,indent=2) )
        fh.close()

        db = dao();
        db.save(data)
        #return "saved"
        return data


    # a method to run every week, say, to check for updates from URL uploads
    # for every collection file, if source is a URL, check it for updates
    def autoupdate(self):
        pass




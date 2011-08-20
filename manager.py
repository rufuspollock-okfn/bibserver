# the new data upload manager

import urllib2
import json
import re
import os
import datetime

from dataset import DataSet
from bibserver.dao import dao

class Manager(object):

    # schedule something
    # for now, does not schedule. just executes.
    def schedule(self,pkg):
        same = False
        if "upfile" in pkg or "data" in pkg:
            pkg["localfile"] = self.store(pkg)
        if "source" in pkg:
            pkg["localfile"], same = self.retrieve(pkg)
        if not same:
            print "indexing"
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

        # no need to store if last modified is before time current one was stored
        if os.path.exists('store/raw/' + tidyname):
            rmod = content.info().getdate('last-modified')
            lmod = datetime.datetime.fromtimestamp(os.path.getmtime('store/raw/' + tidyname))
            # get this to work properly - currently the comparison does not properly succeed
            # how to get the last-modified into a date format?
            if rmod < lmod:
                pass
                #return tidyname, True

        fh = open('store/raw/' + tidyname, 'w')
        fh.write( content.read() )
        fh.close()
        return tidyname, False
    
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
        fh.write( json.dumps(data,indent=2,encoding='8859') )
        fh.close()

        db = dao();
        db.save(data)
        #return "saved"
        return data


    # a method to run every week, say, to check for updates from URL uploads
    # for every collection file, if source is a URL, check it for updates
    def autoupdate(self):
        pass




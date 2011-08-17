# the new data upload manager

import urllib2
import uuid
import json

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
        # for google spreadsheet data, append csv to url and get it
        # this is an easy way to get data from a google spreadsheet
        # the google data API could be used, but here we are assuming public content anyway, so no need
        # to switch to gdata API would require user passing auth credentials
        if pkg["format"] == "google":
            url = url + "&output=csv"
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
            filepath = uploadfile.filename.replace('\\','/')
            filename = filepath.split('/')[-1]
            fh = open('store/raw/' + filename, 'w')
            fh.write( uploadfile.file.read() )
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
        data = self.prepare(data,pkg)

        # write data to file (maybe just for testing)
        fh = open('store/bibjson/' + pkg["localfile"], 'w')
        fh.write( json.dumps(data,indent=2) )
        fh.close()

        db = dao();
        #db.save(data)
        #return "saved"
        return data

    # check prepare the data in various ways
    def prepare(self,data,metadata):
        for index,item in enumerate(data):
            # if collection name provided, check it is in each record, or add it if not
            # if no collection name provided, use source url as collection name
            if "collection" in item:
                pass
            else:
                if metadata["collection"] != "":
                    data[index]["collection"] = [metadata["collection"]]
                elif metadata["url"] != "":
                    data[index]["collection"] = [metadata["url"]]
                else:
                    data[index]["collection"] = ["bibsoup"]

            # give item a uuid
            if "_id" not in item:
                data[index]["_id"] = str( uuid.uuid4() )

            # if people names are provided, e.g. in author fields, check for person records for them
            # if not existing, create one.
            # append person record details to records

        return data

    # a method to run every week, say, to check for updates from URL uploads
    # for every collection file, if source is a URL, check it for updates
    def autoupdate(self):
        pass




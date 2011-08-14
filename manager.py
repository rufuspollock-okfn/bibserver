# the new data upload manager

import urllib2
import uuid

from dataset import DataSet
from dao import dao

class Manager(object):

    # schedule something
    # for now, does not schedule. just executes.
    def schedule(self,pkg):
        if "upfile" in pkg:
            pkg["localfile"] = self.store(pkg)
        if "source" in pkg:
            pkg["localfile"] = self.retrieve(pkg)
        self.index(pkg)
    
    # retrieve from URL into store
    def retrieve(self,pkg):
        # add in checks to see if current local copy is same as remote copy
        source = urllib2.urlopen( pkg["source"] )
        tidyname = url.replace("/","___")
        fh = open('store/raw/' + tidyname, 'w')
        fh.write( source.read() )
        fh.close()
        return tidyname
    
    # store uploaded file
    def store(self,pkg):
        uploadfile = pkg["upfile"]
        filepath = uploadfile.filename.replace('\\','/')
        filename = filepath.split('/')[-1]
        fh = open('store/raw/' + filename, 'w')
        fh.write( uploadfile.file.read() )
        fh.close()
        return filename

    
    # index a file in the store
    def index(self,pkg):
        fh = open('store/raw/' + pkg["localfile"], 'r')
        ds = DataSet()
        data = ds.convert(pkg["source"],pkg["format"])
        data = self.prepare(data,pkg)
        db = dao();
        db.save(data)
        return "saved"

    # check prepare the data in various ways
    def prepare(self,data,metadata):
        for index,item in enumerate(data):
            # if collection name provided, check it is in each record, or add it if not
            # if no collection name provided, use source url as collection name
            if "collection" in item:
                pass
            else:
                if metadata["name"] != "":
                    data[index]["collection"] = [metadata["name"]]
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




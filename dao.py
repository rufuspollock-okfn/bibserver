import json
import couchdb

class dao(object):

    def relax(self,jsonin):
        couch = couchdb.Server(url='http://couch.cottagelabs.com')
        db = couch['bibserver']

        data = json.loads(jsonin)
        
        # should really do a bulk load to couch
        
        for item in data:
            db.save(item)


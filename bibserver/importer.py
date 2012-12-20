# the data import manager
# indexes the records found in the file by upserting via the DAO

import threading
from bibserver.core import app
import bibserver.dao
import bibserver.util as util
from bibserver import auth

class Importer(threading.Thread):

    def __init__(self, data, collid='', creator='', notify_email=''):
        self.data = data
        self.collid = collid
        self.creator = creator
        self.notify_email = notify_email
        threading.Thread.__init__(self)
        
    def run(self):
        '''Import a bibjson collection into the database.'''

        if isinstance(self.data, list):
            metadata = {}
            records = self.data
        else:
            metadata = self.data.get('metadata',{})
            records = self.data.get('records', self.data)
            if isinstance(records, dict):
                records = [records]
            
        if self.collid:
            metadata['_id'] = self.collid
            
        coll = None
        if metadata:
            coll = bibserver.dao.Collection.get(metadata.get('_id',''))
            if coll is not None:
                coll.data.update(metadata)
            else:
                coll = bibserver.dao.Collection(**metadata)
            if coll.owner is None and self.creator:
                coll.data['owner'] = self.creator
            coll.save()
                
        for rec in records:
            if not type(rec) is dict: continue
            for k, v in rec.items():
                if k.lower() != k:
                    rec[k.lower()] = rec[k]
                    del rec[k]
            if coll is not None and coll.id:
                rec['_collection'] = [coll.id]
            else:
                rec['_collection'] = []
            if self.creator:
                rec['_created_by'] = self.creator
        bibserver.dao.Record.bulk(records)
        
        try:
            text = 'Hi there.\n\n' + 'Your import has completed.\n\n'
            if coll and 'SITE_URL' in app.config:
                text += 'As you elected to import to one of your collections, you should be able to find your imported records at '
                text += coll.data['url'] + '\n\n'
            util.send_mail(to=[self.notify_email], _from=app.config.get('EMAIL_FROM','nobody@bibsoup.net'), subject='import completed', text=text)
        except:
            pass

        return True

 

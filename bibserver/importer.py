# the data import manager
# gets an uploaded file or retrieves a file from a URL
# indexes the records found in the file by upserting via the DAO
import json

from flask import Flask, request
from flask.ext.login import login_user, current_user

from bibserver.core import app, current_user
import bibserver.dao
import bibserver.util as util
from bibserver import auth

class Importer(object):

    @classmethod        
    def upload(cls):
        '''Import a bibjson collection into the database.'''

        if request.values.get('source'):
            r = requests.get( request.values['source'].strip() )
            data = json.loads(r.content)
        elif request.files.get('upfile'):
            fileobj = request.files.get('upfile')
            data = json.load(fileobj)
        elif request.json:
            data = request.json
        else:
            abort(409)

        metadata = data.get('metadata',{})
        records = data.get('records', data)
        if isinstance(records,dict):
            records = [records]
            
        if request.values.get('collection'):
            metadata['_id'] = request.values['collection']
            
        coll = False
        if metadata:
            coll = bibserver.dao.Collection.get(metadata.get('_id',''))
            if coll is not None:
                coll.data.update(metadata)
            else:
                coll = bibserver.dao.Collection(**metadata)
            if auth.collection.update(current_user,coll):
                coll.save()
                
        for rec in records:
            if not type(rec) is dict: continue
            for k, v in rec.items():
                if k.lower() != k:
                    rec[k.lower()] = rec[k]
                    del rec[k]
            if coll is not None:
                rec['_collection'] = [coll.id]
            else:
                rec['_collection'] = []
        bibserver.dao.Record.bulk(records)
        
        try:
            text = 'Hi ' + current_user.id + '\n\n' + 'Your import to ' + app.config.get('SERVICE_NAME','our service') + ' has completed.\n\n'
            if coll and app.config['SITE_URL']:
                text += 'As you elected to import to one of your collections, you should be able to find your imported records at '
                text += app.config['SITE_URL'].rstrip('/') + '/' + current_user.id + '/' + coll.slug + '\n\n'
            elif app.config['SITE_URL']:
                text += 'Come and check out all our records, including your new ones, at '
                text += app.config['SITE_URL'].rstrip('/') + '/search'
            util.send_mail(to=[current_user.email], _from=app.config.get('EMAIL_FROM','nobody@bibsoup.net'), subject='import completed', text=text)
        except:
            pass



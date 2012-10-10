# the data import manager
# gets an uploaded file or retrieves a file from a URL
# indexes the records found in the file by upserting via the DAO
import json

from flask import Flask, request
from flask.ext.login import login_user, current_user

import bibserver.dao
import bibserver.util as util

class Importer(object):

    @classmethod        
    def upload(cls):
        '''Import a bibjson collection into the database.'''

        try:

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

            metadata = data.get('metadata',False)
            records = data.get('records', data)

            coll = False
            if request.values.get('collection'):
                coll = bibserver.dao.Collection.get_by_owner_coll(current_user.id, request.values['collection'])
                if coll and metadata:
                    if metadata['collection'] == coll.data['collection']:
                        for k, v in metadata.items():
                            if k.startswith('_'):
                                del metadata[k]
                        coll.data.update(metadata)
                        coll.save()

            for rec in records:
                if not type(rec) is dict: continue
                for k, v in rec.items():
                    if k.lower() != k:
                        rec[k.lower()] = rec[k]
                        del rec[k]
                if coll:
                    rec['_collection'] = [coll.data['_collection']]
                else:
                    rec['_collection'] = []
                rec['_id'] = bibserver.dao.make_id(rec)
                if 'SITE_URL' in app.config:
                    rec['_url'] = app.config['SITE_URL'].rstrip('/') + '/record/' +  rec['_id']
            bibserver.dao.Record.bulk(records)
            
            # TODO: send an email to the owner once complete, or on error

            return collection, records

        except:
            # TODO: email an error notification to the owner
            return False        



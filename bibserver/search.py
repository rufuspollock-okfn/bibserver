
from flask import Flask, request, redirect, abort, make_response
from flask import render_template, flash
import bibserver.dao
from bibserver import auth
import json
from bibserver.config import config
import bibserver.util as util


class Search(object):

    def __init__(self,path,current_user):
        self.path = path.replace(".json","")
        self.current_user = current_user

        self.search_options = {
            'search_url': '/query?',
            'search_index': 'elasticsearch',
            'paging': { 'from': 0, 'size': 10 },
            'predefined_filters': {},
            'facets': config['search_facet_fields'],
            'result_display': config['search_result_display']
        }

        self.parts = self.path.strip('/').split('/')


    def find(self):
        if bibserver.dao.Account.get(self.parts[0]):
            if len(self.parts) == 1:
                return self.account()
            elif len(self.parts) == 2:
                return self.collection() # request for collection
            elif len(self.parts) == 3:
                return self.record() # request for record in collection
        elif len(self.parts) == 1 and self.parts[0] == 'collection':
            return self.collections()
        elif len(self.parts) == 2:
            return self.implicit_facet()


    def implicit_facet(self):
        self.search_options['predefined_filters'][self.parts[0]+config['facet_field']] = self.parts[1]
        return render_template('search/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=None)


    def collections(self):
        # search collection records
        self.search_options['search_url'] = '/query/collection?'
        self.search_options['facets'] = [{'field':'owner','size':100},{'field':'_created','size':100}]
        self.search_options['result_display'] = [[{'pre':'<h3>','field':'label','post':'</h3>'}],[{'field':'description'}],[{'pre':'created by ','field':'owner'}]]
        self.search_options['result_display'] = config['colls_result_display']
        return render_template('collection/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=None)


    def record(self):            
        res = bibserver.dao.Record.query(terms = {
            'owner'+config['facet_field']:self.parts[0],
            'collection'+config['facet_field']:self.parts[1],
            'cid'+config['facet_field']:self.parts[2]
        })
        if res['hits']['total'] == 0:
            res = bibserver.dao.Record.query(terms = {'id'+config['facet_field']:self.parts[2]})

        if res["hits"]["total"] == 0:
            abort(404)
        elif res['hits']['total'] == 1:
            if util.request_wants_json():
                resp = make_response( json.dumps(res['hits']['hits'][0]['_source'], sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                record = bibserver.dao.Record.get(res['hits']['hits'][0]['_id'])
                collection = bibserver.dao.Collection.get_by_owner_coll(record.data['owner'],record.data['collection'])
                if request.method == 'DELETE':
                    if record:
                        if not auth.collection.update(self.current_user, collection):
                            abort(401)
                        record.delete()
                        return ''
                    else:
                        abort(404)
                elif request.method == 'POST':
                    if record:
                        if not auth.collection.update(self.current_user, collection):
                            abort(401)
                        record.data = request.json
                        record.save()
                        return ''
                else:
                    return render_template('record.html', record=json.dumps(res['hits']['hits'][0]['_source']), edit=True)
        else:
            if util.request_wants_json():
                resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                return render_template('record.html', multiple=[i['_source'] for i in res['hits']['hits']])


    def account(self):
        self.search_options['predefined_filters']['owner'+config['facet_field']] = self.parts[0]
        acc = bibserver.dao.Account.get(self.parts[0])

        if request.method == 'DELETE':
            if not auth.user.update(self.current_user,acc):
                abort(401)
            if acc: acc.delete()
            return ''
        elif request.method == 'POST':
            if not auth.user.update(self.current_user,acc):
                abort(401)
            acc.data = request.json
            acc.save()
            return ''
        else:
            if util.request_wants_json():
                if not auth.user.update(self.current_user,acc):
                    abort(401)
                resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                admin = True if auth.user.update(self.current_user,acc) else False
                superuser = True if self.current_user.id == config['super_user'] else False
                return render_template('account/view.html', 
                    current_user=self.current_user, 
                    search_options=json.dumps(self.search_options), 
                    record=json.dumps(acc.data), 
                    admin=admin,
                    account=acc,
                    superuser=superuser
                )


    def collection(self):
        # show the collection that matches parts[1]
        self.search_options['predefined_filters']['owner'+config['facet_field']] = self.parts[0]
        self.search_options['predefined_filters']['collection'+config['facet_field']] = self.parts[1]

        # remove the collection facet
        for count,facet in enumerate(self.search_options['facets']):
            if facet['field'] == 'collection'+config['facet_field']:
                del self.search_options['facets'][count]

        # look for collection metadata
        metadata = bibserver.dao.Collection.get_by_owner_coll(self.parts[0],self.parts[1])
        if metadata:
            if 'display_settings' in metadata:
                # set display settings from collection info
                #search_options = metadata['display_settings']
                pass

        if request.method == 'DELETE':
            if metadata:
                if not auth.collection.update(self.current_user, metadata):
                    abort(401)
                else: metadata.delete()
                return ''
            else:
                if not auth.collection.create(self.current_user, None):
                    abort(401)
                else:
                    size = bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]})['hits']['total']
                    for rid in bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]},size=size)['hits']['hits']:
                        record = bibserver.dao.Record.get(rid['_id'])
                        if record: record.delete()
                    return ''

        elif request.method == 'POST':
            if metadata:
                metadata.data = request.json
                metadata.save()
                return ''
            else: abort(404)
        else:
            if util.request_wants_json():
                out = {"metadata":metadata.data,"records":[]}
                out['metadata']['records'] = len(metadata)
                out['metadata']['query'] = request.url
                for rec in metadata.records:
                    out['records'].append(rec.data)
                resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                admin = True if auth.collection.update(self.current_user, metadata) else False
                return render_template('search/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=metadata, admin=admin)



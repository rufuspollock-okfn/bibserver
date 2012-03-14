
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
        self.search_options['result_display'] = [
            [
                {'pre':'<h3><a href="/','field':'owner','post':'/'},{'field':'collection','post':'">'},{'field':'label','post':'</a></h3>'}
            ],
            [
                {'field':'description'},
                {'pre':' (created by <a href="/','field':'owner','post':'">'},
                {'field':'owner','post':'</a>)'}
            ]
        ]
        return render_template('search/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=None)


    def record(self):
        # POSTs do updates, creates, deletes of records
        if request.method == 'POST':
            # send to POST handler
            pass
            
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
                if request.method == 'DELETE':
                    colln = bibserver.dao.Record.get(self.parts[1])
                    if colln:
                        if not auth.collection.update(self.current_user, colln):
                            abort(401)
                        record = bibserver.dao.Record.get(res['hits']['hits'][0]['_source']['id'])
                        record.delete()
                        return ''
                    else:
                        abort(401)
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
        if hasattr(self.current_user,'id'):
            if self.parts[0] == self.current_user.id:
                acc = bibserver.dao.Account.get(self.parts[0])
                if request.method == 'DELETE':
                    if acc: acc.delete()
                    return ''
                else:
                    if util.request_wants_json():
                        resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
                        resp.mimetype = "application/json"
                        return resp
                    else:
                        return render_template('account/view.html', current_user=self.current_user)
        flash('You are not that user. Or you are not logged in.')
        return redirect('/account/login')


    def collection(self):
        # show the collection that matches parts[1]
        self.search_options['predefined_filters']['owner'+config['facet_field']] = self.parts[0]
        self.search_options['predefined_filters']['collection'+config['facet_field']] = self.parts[1]
        # look for collection metadata
        metadata = bibserver.dao.Collection.query(terms={'owner':self.parts[0],'collection':self.parts[1]})
        if metadata['hits']['total'] != 0:
            metadata = bibserver.dao.Collection.get(metadata['hits']['hits'][0]['_source']['id'])
            if request.method == 'DELETE':
                if not auth.collection.update(self.current_user, metadata):
                    abort(401)
                metadata.delete()
                return ''
            elif request.method == 'POST':
                pass
            elif 'display_settings' in metadata:
                # set display settings from collection info
                #search_options = metadata['display_settings']
                pass
        else:
            # in case a delete is issued against records whose collection object no longer exists
            if request.method == 'DELETE':
                if not auth.collection.create(self.current_user, None):
                    abort(401)
                size = bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]})['hits']['total']
                url = str(config['ELASTIC_SEARCH_HOST'])
                for rid in bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]},size=size)['hits']['hits']:
                    record = bibserver.dao.Record.get(rid['_id'])
                    if record: record.delete()
                return ''
            metadata = False

        for count,facet in enumerate(self.search_options['facets']):
            if facet['field'] == 'collection'+config['facet_field']:
                del self.search_options['facets'][count]
        return render_template('search/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=metadata)


    def update(self):
        if not auth.collection.create(self.current_user, None):
            abort(401)
                    
        newrecord = request.json
        action = "updated"
        recobj = bibserver.dao.Record(**newrecord)
        recobj.save()
        # TODO: should pass a better success / failure output
        resp = make_response( '{"id":"' + recobj.id + '","action":"' + action + '"}' )
        resp.mimetype = "application/json"
        return resp


    def jsonout(results=None, coll=None, facets=None, record=False):
        '''build a JSON response, with metadata unless specifically asked to suppress'''
        # TODO: in some circumstances, people data should be added to collections too.
        out = {"metadata":{}}
        if coll:
            out['metadata'] = coll.data
            out['metadata']['records'] = len(coll)
        out['metadata']['query'] = request.base_url + '?' + request.query_string
        if request.values.get('facets','') and facets:
            out['facets'] = facets
        out['metadata']['from'] = request.values.get('from',0)
        out['metadata']['size'] = request.values.get('size',10)

        if results:
            out['records'] = results

            # if a single record meta default is false
            if record and len(out['records']) == 1 and not request.values.get('meta',False):
                out = out['records'][0]

            # if a search result meta default is true
            meta = request.values.get('meta',True)
            if meta == "False" or meta == "false" or meta == "no" or meta == "No" or meta == 0:
                meta = False
            #if not record and not meta:
            if not record and not meta:
                out = out['records']
                if len(out) == 1:
                    out = out[0]
        elif coll:
            out = coll.data
        else:
            out = {}

        resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp


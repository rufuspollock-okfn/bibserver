import os
import urllib2
import unicodedata
import httplib
import json
from copy import deepcopy
from datetime import datetime

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

import bibserver.dao
import bibserver.util as util
import bibserver.importer
import bibserver.ingest
from bibserver.config import config
from bibserver.core import app, login_manager
from bibserver.view.account import blueprint as account
from bibserver import auth


app.register_blueprint(account, url_prefix='/account')

# NB: the decorator appears to kill the function for normal usage
@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = bibserver.dao.Account.get(userid)
    return out

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = bibserver.dao.Account.get(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = bibserver.dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = bibserver.dao.Account.get(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.route('/query', methods=['GET','POST'])
@app.route('/query/<path:path>')
def query(path='Record'):
    if path.lower() == 'account':
        abort(401)
    klass = getattr(bibserver.dao, path[0].capitalize() + path[1:] )
    qs = request.query_string
    if request.method == "POST":
        qs += "&source=" + json.dumps(dict(request.form).keys()[-1])
    resp = make_response( klass().raw_query(qs) )
    resp.mimetype = "application/json"
    return resp
        
@app.route('/faq')
def content():
    return render_template('home/faq.html')


@app.route('/')
def home():
    return render_template('home/index.html')


# handle or disable uploads
class UploadView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()
        return render_template('upload.html', upload=config["allow_upload"], 
                               ingest_tickets = bibserver.ingest.get_tickets())

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        try:
            collection = request.values.get('collection')
            format=request.values.get('format')
            if request.files.get('upfile'):
                fileobj = request.files.get('upfile')
                if not format:
                    format = bibserver.importer.findformat(fileobj.filename)
            else:
                if not format:
                    format = bibserver.importer.findformat( request.values.get("source").strip('"') )
            
            ticket = bibserver.ingest.IngestTicket(owner=current_user.id, 
                                       source_url=request.values.get("source"),
                                       format=format,
                                       collection=request.values.get('collection'),
                                       description=request.values.get('description'),
                                       )
            # Allow only parsing
            only_parse = request.values.get('only_parse')
            if only_parse:
               ticket['only_parse'] = True
            
            # If the user is uploading a file, update the ticket with the 'downloaded' file
            # And correct source
            if request.files.get('upfile'):
                data = fileobj.read()
                ticket['data_md5'] = bibserver.ingest.store_data_in_cache(data)
                ticket['source_url'] = config['SITE_URL'] + '/ticket/%s/data' % ticket.id
                ticket['state'] = 'downloaded'
            ticket.save()
        except Exception, inst:
            msg = str(inst)
            if app.debug or app.config['TESTING']:
                raise
            flash('error: ' + msg)
            return render_template('upload.html')
        else:
            return redirect('/ticket/'+ticket.id)

class NoUpload(MethodView):
    def get(self):
        return render_template('disabled.html')

    def post(self):
        abort(401)

if config["allow_upload"]:
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))
else:
    app.add_url_rule('/upload', view_func=NoUpload.as_view('upload'))
    

@app.route('/create')
def create():
    return render_template('record.html', record={}, edit=True)


# this is a catch-all that allows us to present everything as a search
# typical catches are /user, /user/collection, /user/collection/record, 
# /collection, /implicit_facet_key/implicit_facet_value
# and any thing else passed as a search
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
def default(path):
    import bibserver.search
    searcher = bibserver.search.Search(path=path,current_user=current_user)
    return searcher.find()

'''
    path = path.replace(".json","")

    search_options = {
        'search_url': '/query?',
        'search_index': 'elasticsearch',
        'paging': { 'from': 0, 'size': 10 },
        'predefined_filters': {},
        'facets': config['search_facet_fields'],
        'result_display': config['search_result_display']
    }

    parts = path.strip('/').split('/')
    if bibserver.dao.Account.get(parts[0]):
        if len(parts) == 1:
            return account(parts[0]) # request is for user account
        elif len(parts) == 2:
            return collection(search_options,parts[0],parts[1]) # request for collection
        elif len(parts) == 3:
            return record(*parts) # request for record in collection
    elif len(parts) == 1 and parts[0] == 'collection':
        # search collection records
        search_options['search_url'] = '/query/collection?'
        search_options['facets'] = [{'field':'owner','size':100},{'field':'_created','size':100}]
        search_options['result_display'] = [[{'pre':'<h3>','field':'label','post':'</h3>'}],[{'field':'description'}],[{'pre':'created by ','field':'owner'}]]
        search_options['result_display'] = [
            [
                {'pre':'<h3><a href="/','field':'owner','post':'/'},{'field':'collection','post':'">'},{'field':'label','post':'</a></h3>'}
            ],
            [
                {'field':'description'},
                {'pre':' (created by <a href="/','field':'owner','post':'">'},
                {'field':'owner','post':'</a>)'}
            ]
        ]
    elif len(parts) == 2:
        # if there are two unknown parts try it as an implicit facet
        search_options['predefined_filters'][parts[0]+config['facet_field']] = parts[1]

    if util.request_wants_json():
        # do search and output as json from DAO
        pass
    else:
        return render_template('search/index.html', current_user=current_user, search_options=json.dumps(search_options), collection=None)


def collection(opts,p0,p1):
    # show the collection that matches parts[1]
    opts['predefined_filters']['owner'+config['facet_field']] = p0
    opts['predefined_filters']['collection'+config['facet_field']] = p1
    # look for collection metadata
    metadata = bibserver.dao.Collection.query(terms={'owner':p0,'collection':p1})
    if metadata['hits']['total'] != 0:
        metadata = bibserver.dao.Collection.get(metadata['hits']['hits'][0]['_source']['id'])
        if request.method == 'DELETE':
            if not auth.collection.update(current_user, metadata):
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
            if not auth.collection.create(current_user, None):
                abort(401)
            size = bibserver.dao.Record.query(terms={'owner':p0,'collection':p1})['hits']['total']
            url = str(config['ELASTIC_SEARCH_HOST'])
            for rid in bibserver.dao.Record.query(terms={'owner':p0,'collection':p1},size=size)['hits']['hits']:
                record = bibserver.dao.Record.get(rid['_id'])
                if record: record.delete()
            return ''
        metadata = False

    for count,facet in enumerate(opts['facets']):
        if facet['field'] == 'collection'+config['facet_field']:
            del opts['facets'][count]
    return render_template('search/index.html', current_user=current_user, search_options=json.dumps(opts), collection=metadata)

def record(user,coll,sid):
    # POSTs do updates, creates, deletes of records
    if request.method == 'POST':
        # send to POST handler
        pass
        
    res = bibserver.dao.Record.query(terms = {'owner'+config['facet_field']:user,'collection'+config['facet_field']:coll,'cid'+config['facet_field']:sid})
    if res['hits']['total'] == 0:
        res = bibserver.dao.Record.query(terms = {'id'+config['facet_field']:sid})
    
    JSON = False
    if JSON:
        return outputJSON(results=[i['_source'] for i in res['hits']['hits']], record=True)
    else:
        if res["hits"]["total"] == 0:
            abort(404)
        elif res["hits"]["total"] != 1:
            return render_template('record.html', multiple=[i['_source'] for i in res['hits']['total']])
        else:
            if request.method == 'DELETE':
                colln = bibserver.dao.Record.get(coll)
                if colln:
                    if not auth.collection.update(current_user, colln):
                        abort(401)
                    record = bibserver.dao.Record.get(res['hits']['hits'][0]['_source']['id'])
                    record.delete()
                    return ''
                else:
                    abort(401)
            else:
                return render_template('record.html', record=json.dumps(res['hits']['hits'][0]['_source']), edit=True)


def account(user):
    if hasattr(current_user,'id'):
        if user == current_user.id:
            if request.method == 'DELETE':
                acc = bibserver.dao.Account.get(user)
                if acc: acc.delete()
                return ''
            else:
                return render_template('account/view.html', current_user=current_user)
    flash('You are not that user. Or you are not logged in.')
    return redirect('/account/login')
    

def update():
    if not auth.collection.create(current_user, None):
        abort(401)
    
    newrecord = request.json
    action = "updated"
    recobj = bibserver.dao.Record(**newrecord)
    recobj.save()
    # TODO: should pass a better success / failure output
    resp = make_response( '{"id":"' + recobj.id + '","action":"' + action + '"}' )
    resp.mimetype = "application/json"
    return resp


def outputJSON(results=None, coll=None, facets=None, record=False):
    # build a JSON response, with metadata unless specifically asked to suppress
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
'''

if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=config['debug'], port=config['port'])


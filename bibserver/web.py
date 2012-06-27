import os
import urllib2
import unicodedata
import httplib
import json
import subprocess
from copy import deepcopy
from datetime import datetime

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flask.ext.login import login_user, current_user

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
            user = bibserver.dao.Account.get(res[0]['_source']['_id'])
            if user:
                login_user(user, remember=False)


@app.route('/query/<path:path>', methods=['GET','POST'])
@app.route('/query/', methods=['GET','POST'])
@app.route('/query', methods=['GET','POST'])
def query(path='Record'):
    pathparts = path.split('/')
    subpath = pathparts[0]
    if subpath.lower() == 'account':
        abort(401)
    klass = getattr(bibserver.dao, subpath[0].capitalize() + subpath[1:] )
    qs = request.query_string
    if request.method == "POST":
        qs += "&source=" + json.dumps(dict(request.form).keys()[-1])
    if len(pathparts) > 1 and pathparts[1] == '_mapping':
        resp = make_response( json.dumps(klass().get_mapping()) )
    else:
        resp = make_response( klass().raw_query(qs) )
    resp.mimetype = "application/json"
    return resp
        
@app.route('/faq')
def content():
    return render_template('home/faq.html')


@app.route('/')
def home():
    data = []
    try:
        colldata = bibserver.dao.Collection.query(sort={"_created.exact":{"order":"desc"}},size=20)
        if colldata['hits']['total'] != 0:
            for coll in colldata['hits']['hits']:
                colln = bibserver.dao.Collection.get(coll['_id'])
                if colln:
                    data.append({
                        'name': colln['label'], 
                        'records': len(colln), 
                        'owner': colln['owner'], 
                        'slug': colln['collection'],
                        'description': colln['description']
                    })
    except:
        pass
    colls = bibserver.dao.Collection.query()['hits']['total']
    records = bibserver.dao.Record.query()['hits']['total']
    users = bibserver.dao.Account.query()['hits']['total']
    print data
    return render_template('home/index.html', colldata=json.dumps(data), colls=colls, records=records, users=users)


@app.route('/users')
@app.route('/users.json')
def users():
    if current_user.is_anonymous():
        abort(401)
    users = bibserver.dao.Account.query(sort={'_id':{'order':'asc'}},size=1000000)
    if users['hits']['total'] != 0:
        accs = [bibserver.dao.Account.get(i['_source']['_id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {"collections":len(acc.collections),"_id":acc["_id"]}
            try:
                user['_created'] = acc['_created']
                user['description'] = acc['description']
            except:
                pass
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/users.html',users=users)
    
# handle or disable uploads
class UploadView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to upload a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()        
        return render_template('upload.html',
                               parser_plugins=bibserver.ingest.get_plugins().values())

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        try:
            if not request.values.get('collection',None):
                flash('You need to provide a collection name.')
                return redirect('/upload')
            if not request.values.get('source',None):
                if not request.files.get('upfile',None):
                    if not request.json:
                        flash('You need to provide a source URL or an upload file.')
                        return redirect('/upload')
                
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
            
            license = request.values.get('license')
            if license: ticket['license'] = license
            
            # If the user is uploading a file, update the ticket with the 'downloaded' file
            # And correct source
            if request.files.get('upfile'):
                data = fileobj.read()
                ticket['data_md5'] = bibserver.ingest.store_data_in_cache(data)
                ticket['source_url'] = config.get('SITE_URL','') + '/ticket/%s/data' % ticket.id
                ticket['state'] = 'downloaded'
            
            # if user is sending JSON, update the ticket with the received JSON
            if request.json:
                data = request.json
                ticket['data_md5'] = bibserver.ingest.store_data_in_cache(json.dumps(data))
                ticket['source_url'] = config.get('SITE_URL','') + '/ticket/%s/data' % ticket.id
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

# handle or disable uploads
class CreateView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()        
        return render_template('create.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)

        # create the new collection for current user
        coll = {
            'label' : request.values.get('collection'),
            'license' : request.values.get('license')
        }
        i = bibserver.importer.Importer(current_user)
        collection, records = i.index(coll, {})
        return redirect(collection['owner'] + '/' + collection['collection'])

# a class for use when upload / create are disabled
class NoUploadOrCreate(MethodView):
    def get(self):
        return render_template('disabled.html')

    def post(self):
        abort(401)    

# set the upload / create views as appropriate
if config["allow_upload"]:
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))
    app.add_url_rule('/create', view_func=CreateView.as_view('create'))
else:
    app.add_url_rule('/upload', view_func=NoUploadOrCreate.as_view('upload'))
    app.add_url_rule('/create', view_func=NoUploadOrCreate.as_view('create'))


# set the route for receiving new notes
@app.route('/note', methods=['GET','POST'])
@app.route('/note/<nid>', methods=['GET','POST','DELETE'])
def note(nid=''):
    if current_user.is_anonymous():
        abort(401)

    elif request.method == 'POST':
        newnote = bibserver.dao.Note()
        newnote.data = request.json
        newnote.save()
        return redirect('/note/' + newnote.id)

    elif request.method == 'DELETE':
        note = bibserver.dao.Note.get(nid)
        note.delete()
        return redirect('/note')

    else:
        thenote = bibserver.dao.Note.get(nid)
        if thenote:
            resp = make_response( json.dumps(thenote.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            abort(404)


# this is a catch-all that allows us to present everything as a search
# typical catches are /user, /user/collection, /user/collection/record, 
# /implicit_facet_key/implicit_facet_value
# and any thing else passed as a search
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
def default(path):
    import bibserver.search
    searcher = bibserver.search.Search(path=path,current_user=current_user)
    return searcher.find()


if __name__ == "__main__":
    if config["allow_upload"]:
        bibserver.ingest.init()
        if not os.path.exists('ingest.pid'):
            ingest=subprocess.Popen(['python', 'bibserver/ingest.py'])
            open('ingest.pid', 'w').write('%s' % ingest.pid)
    try:
        bibserver.dao.init_db()
        app.run(host='0.0.0.0', debug=config['debug'], port=config['port'])
    finally:
        if os.path.exists('ingest.pid'):
            os.remove('ingest.pid')

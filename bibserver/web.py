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


@app.route('/query/', methods=['GET','POST'])
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
    data = []
    try:
        colldata = bibserver.dao.Collection.query(sort={"_created":{"order":"desc"}})
        if colldata['hits']['total'] != 0:
            for coll in colldata['hits']['hits']:
                colln = bibserver.dao.Collection.get(coll['_id'])
                if colln:
                    data.append({
                        'name': colln['label'], 
                        'records': len(colln), 
                        'owner': colln['owner'], 
                        'slug': colln['collection'] 
                    })
    except:
        pass
    colls = bibserver.dao.Collection.query()['hits']['total']
    records = bibserver.dao.Record.query()['hits']['total']
    return render_template('home/index.html', colldata=json.dumps(data), colls=colls, records=records)


# handle or disable uploads
class UploadView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()        
        return render_template('upload.html', upload=config["allow_upload"], 
                               ingest_tickets = bibserver.ingest.get_tickets(),
                               parser_plugins=bibserver.ingest.PLUGINS.values())

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


if __name__ == "__main__":
    if config["allow_upload"]:
        bibserver.ingest.init()
        if not os.path.exists('ingest.pid'):
            ingest=subprocess.Popen(['python', 'bibserver/ingest.py'])
            open('ingest.pid', 'w').write('%s' % ingest.pid)
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=config['debug'], port=config['port'])
    if os.path.exists('ingest.pid'):
        os.remove('ingest.pid')

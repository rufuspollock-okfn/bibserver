import os
import urllib2
import unicodedata
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401


@app.route('/query/<path:path>', methods=['GET','POST'])
@app.route('/query/', methods=['GET','POST'])
@app.route('/query', methods=['GET','POST'])
@util.jsonp
def query(path='Record'):
    pathparts = path.split('/')
    subpath = pathparts[0]
    if subpath.lower() == 'account':
        abort(401)
    klass = getattr(bibserver.dao, subpath[0].capitalize() + subpath[1:] )
    if len(pathparts) > 1 and pathparts[1] == '_mapping':
        resp = make_response( json.dumps(klass().query(endpoint='_mapping')) )
    elif len(pathparts) == 2 and pathparts[1] not in ['_mapping','_search']:
        if request.method == 'POST':
            abort(401)
        else:
            rec = klass().get(pathparts[1])
            if rec:
                resp = make_response( rec.json )
            else:
                abort(404)
    else:
        if request.method == "POST":
            if request.json:
                qs = request.json
            else:
                try:
                    qs = dict(request.form).keys()[-1]
                except:
                    abort(411)
        elif 'q' in request.values:
            qs = {'query': {'query_string': { 'query': request.values['q'] }}}
        elif 'source' in request.values:
            qs = json.loads(urllib2.unquote(request.values['source']))
        else: 
            qs = request.query_string
        for item in request.values:
            if item not in ['q','source']:
                qs[item] = request.values[item]
        resp = make_response( json.dumps(klass().query(q=qs, terms='')) )
    resp.mimetype = "application/json"
    return resp
        

@app.route('/')
def home():
    data = []
    try:
        colldata = bibserver.dao.Collection.query(sort={"_created.exact":{"order":"desc"}},size=1000)
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
    return render_template('home/index.html', colldata=json.dumps(data), colls=colls, records=records, users=users)


# upload from a bibjson file
class UploadView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to upload a collection.')
            return redirect('/account/login')
        return render_template('upload.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(403)
        elif not request.values.get('source',False) and not request.files.get('upfile',False) and not request.json:
            flash('Sorry, you need to provide a source URL or a source file (or POST some JSON via the API).')        
        else:
            bibserver.importer.Importer.upload()
            flash('Thanks. Your records are being uploaded. Please check back soon for updates.', 'success')
        return render_template('upload.html')
            
# create new collection / record
class CreateView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        else:
            return render_template('create.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        elif request.values.get('collection',False):
            # create a new collection
            # new records are POSTed directly to /record
            coll = bibserver.dao.Collection.get(current_user.id + '_' + request.values.get('collection'))
            if coll:
                flash('Sorry! You already have a collection named ' + request.values.get('collection'))
                return
            else:
                collection = bibserver.dao.Collection(
                    collection = request.values.get('collection'),
                    label = request.values.get('collection'),
                    description = request.values.get('description',''),
                    license = request.values.get('license',''),
                    owner = current_user.id
                )
                collection.save()
                return redirect(collection.data['owner'] + '/' + collection.data['collection'])

# a class for use when upload / create are disabled
class NoUploadOrCreate(MethodView):
    def get(self):
        return render_template('disabled.html')
    def post(self):
        abort(403)

# set the upload / create views as appropriate
if app.config.get("ALLOW_UPLOAD",False):
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))
    app.add_url_rule('/create', view_func=CreateView.as_view('create'))
else:
    app.add_url_rule('/upload', view_func=NoUploadOrCreate.as_view('upload'))
    app.add_url_rule('/create', view_func=NoUploadOrCreate.as_view('create'))


# set the route for viewing records
@app.route('/record', methods=['GET','POST'])
@app.route('/record/<rid>', methods=['GET','POST','DELETE'])
@util.jsonp
def record(rid=''):
    rec = bibserver.dao.Record.get(rid.replace(".json",""))
    if request.method == 'DELETE':
        if rec:
            if not current_user.is_super():
                abort(403)
            else:
                rec.delete()
        else:
            abort(404)
    elif request.method == 'POST':
        if current_user.is_anonymous() or not app.config.get("ALLOW_UPLOAD",False):
            abort(403)
        try:
            if not rec:
                rec = bibserver.dao.Record()
            if len(request.json):
                rec.data = request.json
                rec.save()
                resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                abort(400)
        except:
            abort(400)
    elif rec and util.request_wants_json():
        resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif rec:        
        # render the record with all extras
        return render_template('record.html', rec=rec )
    else:
        abort(404)


# show all the collections
@app.route('/collections')
@app.route('/collections.json')
@util.jsonp
def collections():
    if util.request_wants_json():
        res = bibserver.dao.Collection.query(size=1000000)
        colls = [i['_source'] for i in res['hits']['hits']]
        resp = make_response( json.dumps(colls, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        search_options = deepcopy(app.config['FACETVIEW'])
        search_options['search_url'] = '/query/collection?'
        search_options['result_display'] = app.config['COLLECTIONS_RESULT_DISPLAY']
        search_options["searchwrap_start"] = '<div id="facetview_results" class="clearfix">'
        search_options["searchwrap_end"] = "</div>"
        search_options["resultwrap_start"] = '<div class="span3 img thumbnail result_box" style="margin-bottom:10px;height:100px;overflow:hidden;"><div class="result_info">'
        search_options["resultwrap_end"] = "</div></div>"
        search_options["paging"]["size"] = 12
        return render_template('collection/index.html', current_user=current_user, search_options=json.dumps(search_options), collection=None)


# this is a catch-all that allows us to present everything as a search
# typical catches are /user, /user/collection, /user/collection/record, 
# /implicit_facet_key/implicit_facet_value
# and any thing else passed as a search
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
@util.jsonp
def default(path):
    search_options = deepcopy(app.config['FACETVIEW'])
    search_options['result_display'] = deepcopy(app.config['SEARCH_RESULT_DISPLAY'])

    parts = path.strip('/').replace(".json","").split('/')

    implicit = ''
    if bibserver.dao.Account.get(parts[0]):
        return account(search_options,parts,path)
    elif len(parts) == 1 and parts[0] != 'search':
        search_options['q'] = parts[0]
    elif len(parts) == 2:
        search_options['predefined_filters'] = {"implicit": {"term": {parts[0]+app.config['FACET_FIELD']: parts[1]}}}
        for count,facet in enumerate(search_options['facets']):
            if facet['field'] == parts[0]+app.config['FACET_FIELD']:
                del search_options['facets'][count]
        implicit = parts[0]+': ' + parts[1]

    if util.request_wants_json():
        res = bibserver.dao.Record.query()
        resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        search_options['facets'] = deepcopy(app.config['ALL_SEARCH_FACET_FIELDS'])
        return render_template('search/index.html', current_user=current_user, search_options=json.dumps(search_options), implicit=implicit, collection=None)


# present info about a given user and their collections
# called from within the above default search, when the path is an account path
# done this way to enable flexible search paths first
def account(search_options,parts,path):
    acc = bibserver.dao.Account.get(parts[0])
    if len(parts) == 1:
        if request.method == 'DELETE' and acc and auth.user.update(current_user,acc):
            acc.delete()
            abort(404)
        elif request.method == 'POST' and auth.user.update(current_user,acc):
            info = request.json
            if info.get('_id',False):
                if info['_id'] != parts[0]:
                    acc = bibserver.dao.Account.get(info['_id'])
                else:
                    info['api_key'] = acc.data['api_key']
                    info['_created'] = acc.data['_created']
                    info['collection'] = acc.data['collection']
                    info['owner'] = acc.data['collection']
            acc.data = info
            if 'password' in info and not info['password'].startswith('sha1'):
                acc.set_password(info['password'])
            acc.save()
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        elif util.request_wants_json() and auth.user.update(current_user,acc):
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            admin = True if auth.user.update(current_user,acc) else False
            if not admin:
                flash('You are not logged in as ' + acc.id + '. Use the <a href="/account/login">login page</a> if you need to change this.')
            return render_template('account/view.html', 
                current_user=current_user, 
                search_options=json.dumps(search_options), 
                record=json.dumps(acc.data), 
                recordcount = bibserver.dao.Record.query(terms={'owner':acc.id})['hits']['total'],
                collcount = bibserver.dao.Collection.query(terms={'owner':acc.id})['hits']['total'],
                admin = admin,
                account=acc,
                superuser=auth.user.is_super(current_user)
            )
    elif len(parts) == 2:
        search_options['predefined_filters'] = {"owner": {"term": {'owner': parts[1]}}}
        search_options['facets'] = deepcopy(app.config['INCOLL_SEARCH_FACET_FIELDS'])
        coll = bibserver.dao.Collection.get_by_owner_coll(parts[0], parts[1])
        if request.method == 'DELETE' and coll and auth.user.update(current_user,coll):
            coll.delete()
            abort(404)
        elif request.method == 'POST':
            if not coll:
                coll = bibserver.dao.Collection()
            elif not auth.user.update(current_user,coll):
                abort(401)
            if 'collection' in request.json:
                if isinstance('list',request.json['collection']):
                    request.json['collection'] = coll.data['collection'].update(request.json['collection'])
                else:
                    request.json['collection'] = coll.data['collection'].append(request.json['collection'])
            coll.data = request.json
            coll.save()
            resp = make_response( json.dumps(coll.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        elif util.request_wants_json() and coll is not None:
            resp = make_response( json.dumps(coll.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        elif coll is not None:
            search_options['predefined_filters'] = {"coll": {"term": {'collection': parts[1]}}}
            for count,facet in enumerate(search_options['facets']):
                if facet['field'] == 'collection'+app.config['FACET_FIELD']:
                    del search_options['facets'][count]
            if not len(coll):
                flash('Your collection appears to be empty. Go and search for some records to add to it, or create or upload some new ones.')
            owner = True if coll.owner == current_user.id else False
            return render_template('search/index.html', current_user=current_user, search_options=json.dumps(search_options), implicit=None, collection=coll, owner=owner)
        else:
            abort(404)
    elif len(parts) == 3:
        coll = bibserver.dao.Collection.get_by_owner_coll(parts[0],parts[1])
        rec = bibserver.dao.Record.get(parts[2])
        if request.method == 'DELETE' and coll and auth.user.update(current_user,coll):
            rec.data['collection'].remove(parts[1])
            rec.save()
            return ''
        elif request.method == 'POST' and auth.user.update(current_user,coll):
            rec.data['collection'].append(parts[1])
            rec.save()
            return ''
        else:
            return redirect('/record/' + path.split('/')[-1] + '?' + request.query_string)


if __name__ == "__main__":
    app.run(host=app.config['HOST'], debug=app.config['DEBUG'], port=app.config['PORT'])



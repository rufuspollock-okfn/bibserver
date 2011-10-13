import os
import urllib2
from copy import deepcopy
import unicodedata
import httplib

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

import bibserver.dao
from bibserver.config import config
import bibserver.iomanager
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
            user = bibserver.dao.Account.get(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.route('/')
def home():
    # get list of available collections
    try:
        result = bibserver.dao.Collection.query(q="*",sort={"created":{"order":"desc"}})
        if result["hits"]["total"] != 0:
            colls = [i["_source"]  for i in result["hits"]["hits"]]
    except:
        colls = None
        counts = None
    return render_template('home/index.html', colls=colls, upload=config["allow_upload"] )

@app.route('/account/<user>')
def account(user):
    if hasattr(current_user,'id'):
        if user == current_user.id:
            return render_template('account/view.html',current_user=current_user)

    flash('You are not that user. Or you are not logged in.')
    return redirect('/account/login')


@app.route('/content/<path:path>')
def content(path):
    return render_template('home/content.html', page=path)


@app.route('/record/<collid>/<path:path>')
def record(collid,path):
    JSON = False
    if path.endswith(".json") or path.endswith(".bibjson") or request.values.get('format',"") == "json" or request.values.get('format',"") == "bibjson":
        path = path.replace(".bibjson","").replace(".json","")
        JSON = True

    res = bibserver.dao.Record.query(q='collection:"' + collid + '" AND citekey:"' + path + '"')
    if res["hits"]["total"] == 0:
        recorddict = bibserver.dao.Record.get(path)
        if not recorddict:
            abort(404)
    elif res["hits"]["total"] == 1:
        recorddict = res["hits"]["hits"][0]["_source"]
    else:
        recorddict = res["hits"]["hits"][0]["_source"]
        #return render_template('record.html', msg="hmmm... there is more than one record in this collection with that id...")
    
    if JSON:
        return outputJSON(results=recorddict, coll=collid)

    return render_template('record.html', record=recorddict)


@app.route('/query', methods=['GET','POST'])
def query():
    qs = request.query_string
    if request.method == "GET":
        if request.values.get('delete','') and request.values.get('q',''):
            resp = make_response( bibserver.dao.Record.delete_by_query(request.values.get('q')) )
        else:
            resp = make_response( bibserver.dao.Record.raw_query(qs) )
    if request.method == "POST":
        qs += "&source=" + json.dumps(dict(request.form).keys()[-1])
        resp = make_response( bibserver.dao.Record.raw_query(qs) )
    resp.mimetype = "application/json"
    return resp

class UploadView(MethodView):
    '''The upload view.

    upload from URL provided in source, or from file upload button, or from
    POST default format is bibtex, but accept other format specifications via
    format default upload is a collection, but could also be person or group
    record
    '''
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()
        return render_template('upload.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        importer = bibserver.importer.Importer(owner=current_user)
        try:
            collection, records = importer.upload_from_web(request)
        except Exception, inst:
            msg = str(inst)
            if app.debug or app.config['TESTING']:
                raise
            return render_template('upload.html', msg=msg)
        else:
            # TODO: can we be sure that current_user is also the owner
            # e.g. perhaps user has imported to someone else's collection?
            flash('Successfully created collection and imported %s records' %
                    len(records))
            return redirect('/%s/%s/' % (current_user.id, collection['id']))


# enable upload unless not allowed in config
if config["allow_upload"] == "YES":
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))


@app.route('/search')
@app.route('/<path:path>')
def search(path=''):

    JSON = False
    if path.endswith(".json") or path.endswith(".bibjson") or request.values.get('format',"") == "json" or request.values.get('format',"") == "bibjson":
        path = path.replace(".bibjson","").replace(".json","")
        JSON = True

    facet_fields = []
    for item in config["facet_fields"]:
        new = { "key": item['key']+config["facet_field"], "size": item.get('size',100), "order": item.get('order','count') }
        facet_fields.append(new)
    showkeys = request.values.get('showkeys',None)

    args = {"terms":{},"facet_fields" : facet_fields}
    if 'from' in request.values:
        args['start'] = request.values.get('from')
    if 'size' in request.values:
        args['size'] = request.values.get('size')
    if 'sort' in request.values:
        if request.values.get("sort") != "..." and request.values.get("sort") != "":
            args['sort'] = {request.values.get('sort')+config["facet_field"] : {"order" : request.values.get('order','asc')}}
    if 'q' in request.values:
        if len(request.values.get('q')) > 0:
            args['q'] = request.values.get('q')    
    for param in request.values:
        if param in [i['key'] for i in config["facet_fields"]]:
            vals = json.loads(unicodedata.normalize('NFKD',urllib2.unquote(request.values.get(param))).encode('utf-8','ignore'))
            args["terms"][param + config["facet_field"]] = vals
    
    collections = False
    incollection = False 
    implicit_key = False
    implicit_value = False
    if path != '' and not path.startswith("search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) == 2:
            # if first bit is a user ID then this is a collection
            if bibserver.dao.Account.get(bits[0]):
                incollection = bibserver.dao.Collection.get(bits[1])
                bits[0] = 'collection'
            # otherwise its a normal implicit facet
            args['terms'][bits[0]+config["facet_field"]] = [bits[1]]
            implicit_key = bits[0]
            implicit_value = bits[1]
        elif len(bits) == 1 and bits[0] == "collections":
            # it is a request for the collections page
            collections = True
        
    if collections:
        results = bibserver.dao.Collection.query(**args)
    else:
        results = bibserver.dao.Record.query(**args)
    io = bibserver.iomanager.IOManager(results, args, facet_fields, showkeys, incollection, implicit_key, implicit_value, path)

    if JSON:
        return outputJSON(results=results, coll=incollection)
    elif collections:
        return render_template('collections/index.html', io=io)
    else:
        return render_template('search/index.html', io=io)

def outputJSON(results=None, coll=None):
    '''build a JSON response, with metadata unless specifically asked to suppress'''
    meta = request.values.get('meta',True)
    # TODO: in some circumstances, people data should be added to collections too.
    if meta != "False" and meta != "false" and meta != "no" and meta != "No":
        out = {"metadata":{}}
        if coll:
            out['metadata'] = bibserver.dao.Collection.query(q='"'+coll+'"')['hits']['hits'][0]['_source']
        out['metadata']['query'] = request.base_url + '?' + request.query_string
        out['records'] = [i['_source'] for i in results['hits']['hits']]
        if request.values.get('facets','') and results['facets']:
            out['facets'] = results['facets']
        out['metadata']['from'] = request.values.get('from',0)
        out['metadata']['size'] = request.values.get('size',10)
    else:
        out = [i['_source'] for i in results['hits']['hits']]
    resp = make_response( json.dumps(out, indent=4) )
    resp.mimetype = "application/json"
    return resp

if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=True)


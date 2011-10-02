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


@app.route('/')
def home():
    # get list of available collections
    try:
        result = bibserver.dao.Collection.query(q="*",sort={"created":{"order":"desc"}})
        if result["hits"]["total"] != 0:
            colls = [i["_source"]["label"] for i in result["hits"]["hits"]]
    except:
        colls = None
    return render_template('home/index.html', colls=colls, upload=config["allow_upload"] )


@app.route('/content/<path:path>')
def content(path):
    return render_template('home/content.html', page=path)


@app.route('/collection/<collid>/<path:path>')
def record(collid,path):
    JSON = False
    if path.endswith(".json") or path.endswith(".bibjson") or request.values.get('format',"") == "json" or request.values.get('format',"") == "bibjson":
        path = path.replace(".bibjson","").replace(".json","")
        JSON = True

    res = bibserver.dao.Record.query(q='collection:"' + collid + '" AND citekey:"' + path + '"')
    if res["hits"]["total"] == 0:
        abort(404)
    if res["hits"]["total"] > 1:
        return render_template('record.html', msg="hmmm... there is more than one record in this collection with that id...")
    recorddict = res["hits"]["hits"][0]["_source"]
    
    if JSON:
        resp = make_response( json.dumps( recorddict, indent=4 ) )
        resp.mimetype = "application/json"
        return resp

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
            return redirect('/%s/%s/' % (current_user.id, collection['slug']))


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

    # read args from config and params    
    args = {"terms":{},"facet_fields" : [i + config["facet_field"] for i in config["facet_fields"]]}
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
        if param in config["facet_fields"]:
            vals = json.loads(unicodedata.normalize('NFKD',urllib2.unquote(request.values.get(param))).encode('utf-8','ignore'))
            args["terms"][param + config["facet_field"]] = vals
    
    # get implicit facet
    c = {'implicit_facet': {}}
    results = None
    if path != '' and not path.startswith("search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) == 2:
            # its an implicit facet
            args['terms'][bits[0]+config["facet_field"]] = [bits[1]]
            c['implicit_facet'][bits[0]] = bits[1]
        elif len(bits) == 1 and bits[0] == "collection":
            results = bibserver.dao.Collection.query(**args)
        
    # get results and render
    if not results:
        results = bibserver.dao.Record.query(**args)
    args['path'] = path
    c['io'] = bibserver.iomanager.IOManager(results, args)

    if JSON:
        resp = make_response( json.dumps(c['io'].set(), indent=4 ) )
        resp.mimetype = "application/json"
        return resp

    return render_template('search/index.html', c=c)


if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=True)


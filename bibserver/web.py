import os
from datetime import datetime
import urllib2
from copy import deepcopy
import unicodedata
import httplib

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

import bibserver.dao
from bibserver.config import config
import bibserver.iomanager
import bibserver.importer
from bibserver.core import app, login_manager
from bibserver.view.account import blueprint as account

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


@app.route('/')
def home():
    # get list of available collections
    try:
        result = bibserver.dao.Record.query(q="type.exact:collection",sort={"received.exact":{"order":"desc"}})
        if result["hits"]["total"] != 0:
            colls = [i["_source"]["collection"] for i in result["hits"]["hits"]]
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
    if request.method == "GET":
        resp = make_response( bibserver.dao.Record.raw_query(request.query_string) )
        if request.values.get('delete','') and request.values.get('q',''):
            resp = make_response( bibserver.dao.Record.delete_by_query(request.values.get('q')) )
        resp.mimetype = "application/json"
        return resp

    if request.method == "POST":
        if request.values.get('callback',''):
            # this will fail if a POST is done to a URL that has more than just a callback param in the GET
            # why is it so hard to get the POST data object out of flask? Is there not a key for it? 
            callback = request.values["callback"]
            data = json.dumps(dict(request.form).keys()[1])
        else:
            data = json.dumps(dict(request.form).keys()[0])
            callback = ""
        host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
        db_name = config['ELASTIC_SEARCH_DB']
        fullpath = '/' + db_name + '/record/_search'
        c =  httplib.HTTPConnection(host)
        c.request('POST', fullpath, data)
        if callback:
            resp = make_response(callback + '(' + c.getresponse().read() + ')')
        else:
            resp = make_response(c.getresponse().read())
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
        if request.values.get("source") is not None:
            return self.post()
        return render_template('upload.html')

    def post(self):
        pkg = self.package()
        if self.validate(pkg):
            importer = bibserver.importer.Importer()
#            try:
            res = importer.upload(pkg)
            if res != "DUPLICATE":
                if "collection" in pkg:
                    return redirect('/collection/' + pkg["collection"])
                msg = "Your records were uploaded but no collection name could be discerned."
            elif res == "DUPLICATE":
                msg = "The collection name you specified is already in use."
                msg += "<br />Please use another collection name."
            else:
                msg = "Sorry! There was an indexing error. Please try again."                    
#            except:
#                msg = 'Sorry! There was an error indexing your collection. Please try again.'
        else:
            msg = 'Your upload failed to validate. Please try again.'
        return render_template('upload.html', msg=msg)

    def validate(self, pkg):
        '''validate the submission before proceeding'''
        if "source" in pkg or "upfile" in pkg or "data" in pkg:
            return True
        return False
    
    def package(self):
        '''make package with: 
            format of upload (default to bibtex)
            collection name (default to version of filename)
            email address (for a file upload)
            source, upfile, or data, depending on if URL, upload, or POST
            date received
        '''
        pkg = dict()
        if request.values.get("source"):
            pkg["source"] = urllib2.unquote(request.values.get("source"))
            pkg["format"] = self.findformat(pkg["source"])
        if request.files.get('upfile'):
            pkg["upfile"] = request.files.get('upfile')
            pkg["format"] = self.findformat(str(pkg["upfile"].filename))
        if request.values.get('format'):
            pkg["format"] = request.values.get('format')
        if request.values.get('data'):
            pkg["data"] = request.values['data']
        if request.values.get("collection"):
            pkg["collection"] = request.values.get("collection")
        pkg["email"] = request.values.get("email", None)
        pkg["received"] = str(datetime.now())
        return pkg

    def findformat(self,filename):
        if filename.endswith(".json"): return "json"
        if filename.endswith(".bibjson"): return "bibjson"
        if filename.endswith(".bibtex"): return "bibtex"
        if filename.endswith(".bib"): return "bibtex"
        if filename.endswith(".csv"): return "csv"
        return "bibtex"

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
    if path != '' and not path.startswith("search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) == 2:
            # its an implicit facet
            args['terms'][bits[0]+config["facet_field"]] = [bits[1]]
            c['implicit_facet'][bits[0]] = bits[1]
        elif len(bits) == 1:
            # send request through as an implicit facet on type, if said type exists
            qry = 'type' + config["facet_field"] + ':' + bits[0]
            check = bibserver.dao.Record.query(q=qry,size=1)
            if check["hits"]["total"] != 0:
                c['implicit_facet']["type"] = bits[0]
                args['terms']["type"+config["facet_field"]] = [bits[0]]
            else:
                # otherwise just show a listing of the facet values for that key
                if 'q' in args:
                    qryval = args['q']
                else:
                    qryval = "*:*"
                result = bibserver.dao.Record.query(q=qryval,facet_fields=[bits[0]+config["facet_field"]])
                vals = result["facets"][bits[0]+config["facet_field"]]["terms"]
                #return render_template('search/listing.html', vals=vals)
        

    # get results and render
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


import os
from datetime import datetime
import urllib2
from copy import deepcopy

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask.views import View, MethodView
from flaskext.mako import init_mako, render_template

import bibserver.dao
from bibserver.config import config
import bibserver.iomanager
import bibserver.importer

app = Flask(__name__)
app.config['MAKO_DIR'] = 'templates'
init_mako(app)


@app.route('/')
def home():
    # get list of available collections
    result = bibserver.dao.Record.query(q="*:*",facet_fields=["collection"],size=1)
    colls = result.get("facets").get("collection").get("terms")
    upload = False
    return render_template('home/index.html', colls=colls, upload=config["allow_upload"] )


@app.route('/content/<path:path>')
def content(path):
    return render_template('home/content.html', page=path)


@app.route('/collection/<collid>/<path:path>')
def record(collid,path):
    res = bibserver.dao.Record.query(q='collection:"' + collid + '" AND citekey:"' + path + '"')
    if res["hits"]["total"] == 0:
        abort(404)
    if res["hits"]["total"] > 1:
        return render_template('record.html', msg="hmmm... there is more than one record in this collection with that id...")
    recorddict = res["hits"]["hits"][0]["_source"]
    return render_template('record.html', record=recorddict)


@app.route('/query', methods=['GET', 'POST'])
def query():
    resp = make_response( bibserver.dao.Record.raw_query(request.query_string) )
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
            try:
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
            except:
                msg = 'Sorry! There was an error indexing your collection. Please try again.'
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
        if request.files.get('upfile'):
            pkg["upfile"] = request.files.get('upfile')
        if request.values.get('data'):
            pkg["data"] = request.values['data']

        if request.values.get("collection"):
            pkg["collection"] = request.values.get("collection")
        pkg["format"] = request.values.get('format', 'bibtex')
        pkg["email"] = request.values.get("email", None)

        pkg["received"] = str(datetime.now())

        return pkg

# enable upload unless not allowed in config
if config["allow_upload"] == "YES":
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))


@app.route('/search')
@app.route('/<path:path>')
def search(path=''):

    # read args from config and params    
    args = {"terms":{},"facet_fields" : config["facet_fields"]}
    if 'from' in request.values:
        args['start'] = request.values.get('from')
    if 'size' in request.values:
        args['size'] = request.values.get('size')
    if 'q' in request.values:
        if len(request.values.get('q')) > 0:
            args['q'] = request.values.get('q')
    for param in request.values:
        if param in config["facet_fields"]:
            vals = json.loads(urllib2.unquote(request.values.get(param)))
            args["terms"][param] = vals
    
    # get implicit facet
    c = {'implicit_facet': {}}
    if path is not None and not path.startswith("/search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) == 2:
            args['terms'][bits[0]] = [bits[1]]
            c['implicit_facet'][bits[0]] = bits[1]

    # get results and render
    results = bibserver.dao.Record.query(**args)
    args['path'] = path
    c['io'] = bibserver.iomanager.IOManager(results, args)
    return render_template('search/index.html', c=c)


if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=True)


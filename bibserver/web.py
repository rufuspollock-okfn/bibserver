import os
from datetime import datetime
import urllib2

from flask import Flask, jsonify, json, request, redirect, abort
from flask.views import View, MethodView
from flaskext.mako import init_mako, render_template

import bibserver.config
import bibserver.dao
import bibserver.setconfig
import bibserver.resultmanager
import bibserver.urlmanager
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
    return render_template('home/index.html', colls=colls, upload=bibserver.config.config["allow_upload"])


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
    out = bibserver.dao.Record.raw_query(request.query_string)
    # data returned will be json or jsonp
    return out


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
if bibserver.config.config["allow_upload"] == "YES":
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))


@app.route('/search')
@app.route('/search<path:path>')
@app.route('/<path:path>')
def search(path=''):
    c = {} 
    config = bibserver.setconfig.Configuration(bibserver.config.config)
    query = request.args.get('q', '')

    # get the args (if available) out of the request
    a = request.values.get("a")
    if a is not None:
        a = urllib2.unquote(a)
        args = json.loads(a)
    else:
        args = config.get_default_args()

    args['search'] = query
    c['q'] = query
    c['config'] = config
    
    # get implicit facets
    implicit_facets = {}
    if path is not None and not path.startswith("/search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) % 2 == 0:
            config.base_url = config.base_url.replace(config.strip_for_implicit_paths,"") + path
            if not args.has_key('q'):
                args['q'] = {}
            for i in range(0, len(bits), 2):
                field = bits[i]
                value = bits[i+1]
                if args['q'].has_key(field):
                    args['q'][field].append(value)
                else:
                    args['q'][field] = [value]
                if implicit_facets.has_key(field):
                    implicit_facets[field].append(value)
                else:
                    implicit_facets[field] = [value]

    # get results and render
    c['url_manager'] = bibserver.urlmanager.UrlManager(config, args,
            implicit_facets)
    c['implicit_facets'] = implicit_facets
    print c['implicit_facets']
    querydict = convert_query_dict_for_es(args)
    results = bibserver.dao.Record.query(**querydict)
    c['results'] = bibserver.resultmanager.ResultManager(results, config, args)
    return render_template('search/index.html', c=c)


def convert_query_dict_for_es(querydict):
    outdict = {}
    outdict['q'] = querydict['search']
    outdict['facet_fields'] = querydict.get('facet_field', None)
    outdict['terms'] = {}
    for term, values in querydict.get('q', {}).items():
        # only use first value (TODO: can one ever have multi-values?)
        outdict['terms'][term] = values[0]
    outdict['size'] = querydict.get('rows', 10)
    outdict['start'] = querydict.get('start', 0)
    return outdict


if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=True)


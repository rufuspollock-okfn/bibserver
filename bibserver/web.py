import os
from datetime import datetime
import urllib2

from flask import Flask, jsonify, json, request, redirect, abort
from flask.views import View, MethodView
from flaskext.mako import init_mako, render_template

import bibserver.dao
import bibserver.solreyes

app = Flask(__name__)
app.config['MAKO_DIR'] = 'templates'
init_mako(app)

app.register_blueprint(bibserver.solreyes.solreyes_app)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/content/<path:path>')
def content(path):
    return render_template('content.html', page=path)


@app.route('/record/<rid>')
def record(rid):
    recorddict = bibserver.dao.Record.get(rid)
    if recorddict is None:
        abort(404)
    return render_template('record.html', record=recorddict)


@app.route('/query')
def query():
    return bibserver.dao.Record.raw_query(request.query_string)


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
        from bibserver.manager import Manager
        pkg = self.package()
        if self.validate(pkg):
            manager = Manager()
            manager.schedule(pkg)
            msg = 'Thanks! Your file has been scheduled for upload. It will' + \
                'soon be available at <a href="/collection/' + \
                pkg["collection"] + '">http://bibsoup.net/collection/' + pkg["collection"] + '</a>'
            return render_template('index.html', msg=msg)
        else:
            return 'Failed to validate'

    def validate(self, pkg):
        '''validate the submission before proceeding'''
        if "source" in pkg or "upfile" in pkg or "data" in pkg:
            return True
        return False
    
    def package(self):
        '''make package with format of upload, collection name to save as, email to notify
        '''
        pkg = dict()
        pkg["format"] = request.values.get('format', 'bibtex')
        pkg["collection"] = request.values.get("collection", '')
        pkg["notify"] = request.values.get("notify", None)
        # also with source URL / file upload if present
        if request.values.get("source"):
            pkg["source"] = urllib2.unquote(request.values.get("source"))
        upfile = request.files.get('upfile', None)
        if upfile:
            pkg["upfile"] = upfile 

        if request.values.get('data'):
            pkg["data"] = request.values['data']

        # get request info
        pkg["ip"] = request.remote_addr
        pkg["received"] = str(datetime.now())
        return pkg

app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)


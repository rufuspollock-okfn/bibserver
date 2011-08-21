import os
from datetime import datetime
from flask import Flask, jsonify, json, request, redirect, abort
from flask.views import View, MethodView
from flaskext.mako import init_mako, render_template

import bibserver.dao


app = Flask(__name__)
app.config['MAKO_DIR'] = 'templates'
init_mako(app)


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


class UploadView(MethodView):
    '''The uploader controller.

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
        from manager import Manager
        pkg = self.package()
        # for source URL, schedule it for grab and save
        if self.validate(pkg):
            manager = Manager()
            manager.schedule(pkg)
            return render.index(msg='Thanks! Your file ' + 
                ' has been scheduled for upload. It will soon be available at <a href="/collection/' + 
                pkg["collection"] + '">http://bibsoup.net/collection/' + pkg["collection"] + '</a>')

    def validate(self, pkg):
        '''validate the submission before proceeding'''
        if "source" in pkg or "upfile" in pkg or "data" in pkg:
            return True
        return False
    
    def package(self):
        '''make package with format of upload, collection name to save as, email to notify
        '''
        pkg = dict()
        pkg["format"] = "bibtex"
        if request.values.get("format") is not None:
            if request.values.get("format") != "":
                pkg["format"] = request.values.get("format")
        if request.values.get("collection") != "": pkg["collection"] = request.values.get("collection")
        if request.values.get("notify") != "": pkg["notify"] = request.values.get("notify")
        # also with source URL / file upload if present
        if request.values.get("source") != "": pkg["source"] = urllib2.unquote(request.values.get("source"))
        if request.values.get("upfile") is not None:
            if request.values.get("upfile") != "":
                pkg["upfile"] = web.input(upfile={})

        # TODO: reinstate this once we know what web.data() is exactly.
        # if web.data() is not None:
        #    if web.data() != "":
        #        pkg["data"] = web.data()

        # get request info
        pkg["ip"] = request.remote_addr
        pkg["received"] = str(datetime.now())
        return pkg

app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)


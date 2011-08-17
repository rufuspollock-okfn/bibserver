# the main URL access controller

from datetime import datetime
import web
import urllib2

from solreyes import SolrEyesController
from manager import Manager
from dao import dao

import os
from web.contrib.template import render_mako

render = render_mako(
        directories=[os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),],
        input_encoding='utf-8',
        output_encoding='utf-8',
        )

urls = (
    '/','index',
    '/upload(.*)','upload',
    '/admin(.*)','admin',
    '/processing(.*)','processing',
    '/search','SolrEyesController',
    '/query(.*)','query',
    '/content/(.*)','content',
    '/collection','collections',
    '/person','persons',
    '/(.*)','SolrEyesController'
)

app = web.application(urls,globals())

# the front page control
# just show the main page
class index:
    def GET(self):
        return render.index()

class collections:
    def GET(self):
        return "return a list of all collections in HTML or JSON"

class persons:
    def GET(self):
        return "return a list of all persons in HTML or JSON"

# the admin control
# show various admin functions
class admin:
    def GET(self,extra):
        pass

# the processing control
# show details of current and recently finished processes
class processing:
    def GET(self,extra):
        pass

# the query control
# pass incoming GET or POST content to the SOLR or ES query handler
# return the query result directly
class query:
    def GET(self,extra):
        db = dao()
        return db.query(get=web.ctx.query)
    
    def POST(self,extra):
        db = dao()
        return db.query(get=web.ctx.query,data=web.data())

# the uploader control
# upload from URL provided in source, or from file upload button, or from POST
# default format is bibtex, but accept other format specifications via format
# default upload is a collection, but could also be person or group record
class upload:
    def GET(self,extra):
        pkg = self.package(web)
        # for source URL, schedule it for grab and save
        if self.validate(pkg):
            manager = Manager()
            manager.schedule(pkg)
            return render.index(msg='Thanks! Your file ' + pkg["source"] + 
                ' has been scheduled for upload. It will soon be available at <a href="/collection/' + 
                pkg["collection"] + '">http://bibsoup.net/collection/' + pkg["collection"] + '</a>')

        return render.upload()

    def POST(self,extra):
        pkg = self.package(web)
        pkg["data"] = web.data()
        if self.validate(pkg):
            manager = Manager()
            manager.schedule(pkg)
            return "scheduled"
        
        return "please upload"

    # validate the submission before proceeding
    def validate(self,pkg):
        if "source" in pkg:
            return True
        return False
    
    # make package with format of upload, collection name to save as, email to notify
    def package(self,web):
        pkg = dict()
        pkg["format"] = "bibtex"
        if web.input().get("format") is not None: pkg["format"] = web.input().get("format")
        if web.input().get("collection") is not None: pkg["collection"] = web.input().get("collection")
        pkg["notify"] = web.input().get("notify")
        # also with source URL / file upload if present
        if web.input().get("source") is not None: pkg["source"] = urllib2.unquote(web.input().get("source"))
        if web.input().get("upfile") is not None and web.input().get("source") is None: 
            pkg["upfile"] = web.input().get("upfile")
        # get request info
        pkg["ip"] = web.ctx.ip
        pkg["received"] = datetime.now()
        return pkg

# the static page content control
# pass through requests to particular pages of site
# could also pass through to wordpress or similar blog, though not by default
class content:
    def GET(self,page):
        return render.content(page=page)

# show admin info, such as scheduled uploads
class admin:
    def GET(self):
        return "show admin about scheduled uploads etc"

# run it
if __name__ == "__main__": app.run()

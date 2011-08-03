import web
import urllib2

from datasource import DataSource
from dao import dao
from serialisers.JsonSerialiser import JsonSerialiser
from solreyes import SolrEyesController

render = web.template.render('templates/')

urls = (
    '/','index',
    '/upload', 'UploadController',
    '/search','SolrEyesController',
    '/(.*)','SolrEyesController'
)

app = web.application(urls,globals())

class index:
    def GET(self):
        # if passed a source, upload it
        if web.input().get("source"):
            self.upload( web.input().get("source") )

        # otherwise display a default front page
        return render.index(False)
        
    def POST(self):
        # if passed a source, upload it
        if web.input().get("source"):
            self.upload( web.input().get("source") )

        # default to hitting the search result page
        if web.input().get("q") == "":
            raise web.seeother('/search')
        else:
            raise web.seeother('/search?q=' + web.input().get("q"))

    def upload(source):
        # presuming its from bibtex at the moment
        # get the data from the source
        try:
            source = urllib2.unquote(web.input().get("source"))
            ds = DataSource()
            data = ds.import_from(source)
            # save the data
            db = dao();
            #db.save(data)
            return "thanks! we are uploading from " + web.input().get("source")
        except:
            return "sorry. we could not upload from " + web.input().get("source")

class UploadController(object):
    def GET(self):
        # GET can take the source URL and collection name only
        source = web.input().get('source')
        cname = web.input().get("name")
        return self.process_reference_upload(source, cname)
        
    def POST(self):
        # POST can take the source URL OR file upload and collection name
        source = web.input().get('source')
        cname = web.input().get("name")
        return self.process_reference_upload(source, cname)
        
    def process_reference_upload(self, source, cname):
        # presuming its from bibtex at the moment
        # get the data from the source
        try:
            source = urllib2.unquote(source)
            ds = DataSource()
            data = ds.import_from(source)
            
            # save the data
            db = dao();
            db.save(data)
            return "thanks! we are uploading from " + web.input().get("source")
        except:
            return "sorry. we could not upload from " + web.input().get("source")

class record:
    # do conneg here - should pass solreyes if html, should pass JSON object if JSON
    def GET(self,record):
        s = SolrEyesController()
        settings = {"q":{"*":[record]},"base_url":"http://bibserver.cottagelabs.com/record/" + record}
        return s.GET(settings)

class collection:
    # do conneg here - should pass solreyes if html, should pass JSON object if JSON
    def GET(self,collection):
        s = SolrEyesController()
        settings = {"q":{"collection":[collection]},"base_url":"http://bibserver.cottagelabs.com/collection/" + collection}
        return s.GET(settings)

class person:
    # do conneg here - should pass solreyes if html, should pass JSON object if JSON
    def GET(self,person):
        s = SolrEyesController()
        settings = {"q":{"*":[person]},"base_url":"http://bibserver.cottagelabs.com/person/" + person}
        return s.GET(settings)

if __name__ == "__main__": app.run()

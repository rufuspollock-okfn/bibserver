import web
import urllib2

from datasource import DataSource
from dao import dao
from serialisers.JsonSerialiser import JsonSerialiser
from solreyes import SolrEyesController

render = web.template.render('templates/')

urls = (
    '/','index',
    '/search','SolrEyesController',
    '/record/(.*)','record',
    '/collection/(.*)','collection',
    '/person/(.*)','person'
)

app = web.application(urls,globals())

# show splash page  
class index:
    def GET(self):
        # if passed a query param
        if web.input().get("source"):
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

        # otherwise display a default front page
        return render.index(False)

    def POST(self):
        # if passed a source URL from the form
        if web.input().get("source"):
            # presuming its from bibtex at the moment
            # get the data from the source
            source = urllib2.unquote(queries.get('source'))
            ds = DataSource()
            data = ds.import_from(source)
            # save the data
            db = dao()
            #db.save(data)
            return "thanks! we are uploading from " + web.input().get("source")

        if web.input().get("q"):
            raise web.seeother('/search?q=' + web.input().get("q"))
        
        return "posting"

# content-negociate for a record
class record:
    def GET(self,record):
        return "show a record " + record

# content-negociate for a collection
class collection:
    def GET(self,collection):
        return "show a collection " + collection

# content-negociate for a person
class person:
    def GET(self,person):
        return "show a person " + person

if __name__ == "__main__": app.run()

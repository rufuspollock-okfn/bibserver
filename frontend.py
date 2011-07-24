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


        # default to hitting the search result page
        raise web.seeother('/search?q=' + web.input().get("q"))
        
# content-negociate for a record
class record:
    def GET(self,record):
        return "show a record " + record

# pass collections info to the requester
class collection:

    # do conneg here - should pass solreyes if html, should pass JSON object if JSON
    def GET(self,collection):
        s = SolrEyesController()
        settings = {"q":{"collection":[collection]},"base_url":"http://bibserver.cottagelabs.com/collection/" + collection}
        return s.GET(settings)

# content-negociate for a person
class person:
    def GET(self,person):
        # if a string, do a search for the string
        # if a person ID, get the person record
        return "show a person " + person

if __name__ == "__main__": app.run()

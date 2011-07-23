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
        if web.ctx.query:
            queries = dict(item.split("=") for item in str(web.ctx.query.replace("?","")).split("&"))
            # if there is a source param
            if queries.get('source'):
                # presuming its from bibtex at the moment
                # get the data from the source
                source = urllib2.unquote(queries.get('source'))
                ds = DataSource()
                data = ds.import_from(source)
                # save the data
                db = dao();
                db.save(data)
                return "thanks! we are uploading that"

        # otherwise display a default front page
        return render.index(False)

    def POST(self):
        # if passed a source URL from the form
        if True:
            # presuming its from bibtex at the moment
            # get the data from the source
            source = urllib2.unquote(queries.get('source'))
            ds = DataSource()
            data = ds.import_from(source)
            # save the data
            db = dao();
            db.save(data)
            return "thanks! we are uploading that"
        
        # if passed a file to upload
        if False:
            return "thanks! we are uploading that"

    def POST(self): 
        form = myform()
        if not form.validates():
            return render.formtest(form)
        else:
            # read the uploaded file
            ds = DataSource()
            data = ds.read_from(form["source"])
            # save the data
            db = dao();
            db.save(data)
            return "thanks! we are uploading that"

        # go to index of this collection
        return "nothing to do"

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

import web
import urllib2

from datasource import DataSource
from indexer import Indexer
#from dao import dao
from serialisers.JsonSerialiser import JsonSerialiser
from solreyes import SolrEyesController

render = web.template.render('templates/')

urls = (
    '/','index',
    '/bibsoup','SolrEyesController' #,
#    '/bibsoup/record/(.*)','record',
#    '/bibsoup/collection/(.*)','collection',
#    '/bibsoup/person/(.*)','person'
)

app = web.application(urls,globals())

# show splash page  
# should include link to create new
# link to view collection
# stats of collections available
class index:
    def upload(self,url,filename,sourcetype,collname):
        # if url, get raw from url
        if True:
            location = urllib2.unquote(queries.get('loc'))
        
        # if file, get raw from file
        
        # if we already have this loc/file/coll indexed
            # if needs updated
                # update it

        # if loc/file/coll not indexed
        
            # get the datasource
            # will depend on sourcetype
            ds = DataSource()
            d = ds.import_from(location)
        
            # pass to solr
            i = Indexer()
            i.index(d)
        
            # pass to couch    
#            s = JsonSerialiser()
#            j = s.serialise(d)
#            r = dao()
#            r.relax(j)
        
        # go to page with index of the collection
        return "done"

    def GET(self):
        # if passed a location
        if web.ctx.query:
            queries = dict(item.split("=") for item in str(web.ctx.query.replace("?","")).split("&"))
            if queries.get('loc'):
                # pass upload location, source type and name for collection to uploader
                return upload(queries.get('loc'),False,"type","name")

        # otherwise display a default front page
        return render.index(False)

    def POST(self):
        # if passed a location from the form
        if True:
            return upload("location",False,"type","name")
        
        # if passed a file to upload
        if False:
            return upload(False,"filepointer","type","name")

        # go to index of this collection
        return "done"

# the default faceted view across our whole dataset
class bibsoup:
    def GET(self):
        return "hello"

# content-negociate for a record
class record:
    def GET(self):
        return "show a record"

# content-negociate for a collection
class collection:
    def GET(self):
        return "show a collection"

# content-negociate for a person
class person:
    def GET(self):
        return "show a person"

if __name__ == "__main__": app.run()

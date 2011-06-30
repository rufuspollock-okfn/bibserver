import web
import urllib2

from datasource import DataSource
from indexer import Indexer
from dao import dao
from serialisers.JsonSerialiser import JsonSerialiser

render = web.template.render('templates/')

urls = (
    '/','index'
)

app = web.application(urls,globals())

class index:
    def GET(self):
        # if passed a location
        if web.ctx.query:
            queries = dict(item.split("=") for item in str(web.ctx.query.replace("?","")).split("&"))
            if queries.get('loc'):
                # test to see if we already have this loc indexed
                # if so, test if it needs updated
                # update if it needs it
                # call the function that builds the output page
                
                # get the location
                location = urllib2.unquote(queries.get('loc'))
                
                # get the datasource
                ds = DataSource()
                d = ds.import_from(location)
                
                # pass to solr
                i = Indexer()
                i.index(d)
                
                # pass to couch    
                s = JsonSerialiser()
                j = s.serialise(d)
                r = dao()
                r.relax(j)
                
                # fire it to the parser
                return "ta! we will do something with " + location

        # otherwise display a form to accept a URL
        return render.index(False)

if __name__ == "__main__": app.run()

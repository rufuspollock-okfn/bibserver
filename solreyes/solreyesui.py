import web
from solreyes import SolrEyesController

urls = (
	'/.*', 'SolrEyesController'
)

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()


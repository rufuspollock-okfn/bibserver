from nose.tools import assert_equal
import urllib
from base import *
from bibserver import web, ingest
import os


class TestWeb(object):
    @classmethod
    def setup_class(cls):
        web.app.config['TESTING'] = True
        cls.app = web.app.test_client()
        # fixture data
        recdict = fixtures['records'][0]
        cls.record = dao.Record.upsert(recdict)
        Fixtures.create_account()
        config['download_cache_directory'] = 'test/data/downloads'
        ingest.init()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)
        for x in os.listdir('test/data/downloads'):
            os.unlink(os.path.join('test/data/downloads', x))
        os.rmdir('test/data/downloads')

    def test_home(self):
        res = self.app.get('/')
        assert 'BibSoup' in res.data, res.data

    def test_faq(self):
        res = self.app.get('/faq')
        assert 'This service is an example' in res.data, res.data

    def test_record(self):
        res = self.app.get('/' + Fixtures.account.id + '/' + self.record["collection"] + '/' + self.record["_id"] + '.json')
        assert res.status == '200 OK', res.status
        out = json.loads(res.data)
        assert out["id"] == self.record["id"], out

    def test_upload(self):
        res = self.app.get('/upload')
        print res.status
        assert res.status == '302 FOUND', res.status
        res = self.app.get('/upload',
            headers={'REMOTE_USER': Fixtures.account.id}
            )
        assert res.status == '200 OK', res.status
        assert 'upload' in res.data, res.data

    def test_upload_post(self):
        startnum = dao.Record.query()['hits']['total']
        res = self.app.post('/upload?format=bibtex&collection='+urllib.quote_plus('"My Test Collection"'),
            data = {'upfile': (open('test/data/sample.bibtex'), 'sample.bibtex')},
            headers={'REMOTE_USER': Fixtures.account.id}
            )
        assert res.status == '302 FOUND', res.status
        # Now we have to trigger the ingest handling of the ticket
        # which is normally done asynchronously
        for state in ('new', 'downloaded', 'parsed'):
            for t in ingest.get_tickets(state):
                ingest.determine_action(t)
        
        endnum = dao.Record.query()['hits']['total']
        assert_equal(endnum, startnum+1)

    # TODO: re-enable
    # This does not work because login in the previous method appears to
    # persist to this method. Not sure how to fix this ...
    def _test_upload_post_401(self):
        bibtex_data = open('test/data/sample.bibtex').read()
        res = self.app.post('/upload',
            data=dict(
                format='bibtex',
                collection='My Test Collection',
                data=bibtex_data,
                )
            )
        assert res.status == '401 UNAUTHORIZED', res.status

    def test_query(self):
        res = self.app.get('/query')
        assert res.status == '200 OK', res.status

        res = self.app.get('/query?q=title:non-existent')
        assert res.status == '200 OK', res.status
        out = json.loads(res.data)
        assert out['hits']['total'] == 0, out

    def test_accounts_query_inaccessible(self):
        res = self.app.get('/query/account')
        assert res.status == '401 UNAUTHORIZED', res.status

    def test_search(self):
        res = self.app.get('/search?q=tolstoy&format=json')
        assert res.status == '200 OK', res.status
        out = json.loads(res.data)
        assert len(out) == 1, out
        assert "Tolstoy" in out[0]["author"][0]["name"], out

        


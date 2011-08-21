from base import *
from bibserver import web


class TestWeb(object):
    @classmethod
    def setup_class(cls):
        web.app.config['TESTING'] = True
        cls.app = web.app.test_client()
        # fixture data
        recdict = fixtures['records'][0]
        cls.record = dao.Record.upsert(recdict)

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_home(self):
        res = self.app.get('/')
        assert 'BibSoup' in res.data, res.data

    def test_content(self):
        res = self.app.get('/content/caveat')
        assert 'this service is alpha' in res.data, res.data

    def test_record(self):
        res = self.app.get('/record/%s' % self.record.id)
        assert res.status == '200 OK', res.status
        assert 'id - %s' % self.record.id in res.data, res.data

    def test_search(self):
        res = self.app.get('/search')
        # assert res.status == '200 OK', res.status

    def test_upload(self):
        res = self.app.get('/upload')
        assert res.status == '200 OK', res.status


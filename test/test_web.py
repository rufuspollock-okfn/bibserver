from nose.tools import assert_equal

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
        Fixtures.create_account()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_home(self):
        res = self.app.get('/')
        assert 'BibSoup' in res.data, res.data

    def test_content(self):
        res = self.app.get('/content/howto')
        assert 'This website is an example' in res.data, res.data

    def test_record(self):
        res = self.app.get('/collection/' + self.record["collection"] + '/' + self.record["citekey"])
        assert res.status == '200 OK', res.status
        assert '%s' % self.record["citekey"] in res.data, res.data

    def test_upload(self):
        res = self.app.get('/upload')
        assert res.status == '302 FOUND', res.status
        res = self.app.get('/upload',
            headers={'REMOTE_USER': Fixtures.account.id}
            )
        assert res.status == '200 OK', res.status
        assert 'upload' in res.data, res.data

    def test_upload_post(self):
        bibtex_data = open('test/data/sample.bibtex').read()
        startnum = dao.Record.query()['hits']['total']
        res = self.app.post('/upload',
            data=dict(
                format='bibtex',
                collection='My Test Collection',
                data=bibtex_data
                ),
            headers={'REMOTE_USER': Fixtures.account.id}
            )
        assert res.status == '302 FOUND', res.status
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
        assert 'Query endpoint' in res.data, res.data

        res = self.app.get('/query?q=title:non-existent')
        assert res.status == '200 OK', res.status
        out = json.loads(res.data)
        assert out['hits']['total'] == 0, out

    def test_search(self):
        res = self.app.get('/search?q=tolstoy')
        assert res.status == '200 OK', res.status
        assert 'Tolstoy' in res.data, res.data




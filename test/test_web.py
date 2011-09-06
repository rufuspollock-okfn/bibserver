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
        res = self.app.get('/collection/' + self.record["collection"][0] + '/' + self.record["citekey"])
        assert res.status == '200 OK', res.status
        assert 'id - %s' % self.record.id in res.data, res.data

    def test_upload(self):
        res = self.app.get('/upload')
        assert res.status == '200 OK', res.status

    def test_upload_post(self):
        bibtex_data = open('test/data/sample.bibtex').read()
        res = self.app.post('/upload', data=dict(
            format='bibtex',
            data=bibtex_data
            ))
        assert res.status == '200 OK', res.status

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

    def test_queryobject(self):
        indata = {
            'search': u'pitman',
            'rows': 10,
            'q': {u'collection': [u'pitman2']},
            'facet_date': {},
            'facet_range': {},
            'facet_field': [u'author', u'journal',
                u'collection', u'subjects', u'year', u'type']
        }
        outdata = web.convert_query_dict_for_es(indata)
        assert_equal(outdata['size'], 10)
        assert_equal(outdata['terms'], {'collection': 'pitman2'})



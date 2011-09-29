import os
import json
import pprint
from nose.tools import assert_equal

from test.base import fixtures, Fixtures, TESTDB
import bibserver.dao as dao
import bibserver.util as util


class TestDAO:
    @classmethod
    def setup_class(cls):
        Fixtures.create_account()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_01_record(self):
        recdict = fixtures['records'][0]
        record = dao.Record.upsert(recdict)
        outrecord = dao.Record.get(record.id)
        for attr in ['type', 'author']:
            assert record[attr] == recdict[attr], record
            assert outrecord[attr] == recdict[attr], outrecord
    
    def test_02_collection(self):
        label = u'My Collection'
        slug = util.slugify(label)
        colldict = {
            'label': label,
            'slug': slug,
            'owner': Fixtures.account.id
            }
        coll = dao.Collection.upsert(colldict)
        assert coll.id, coll
        assert coll['label'] == label
        # should only be one collection for this account so this is ok
        account_colls = Fixtures.account.collections
        assert coll.id == account_colls[0].id, account_colls
        

class TestDAOQuery:
    @classmethod
    def setup_class(cls):
        for rec in fixtures['records']:
            dao.Record.upsert(rec)

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_query(self):
        out = dao.Record.query()
        assert out['hits']['total'] == 2

    def test_query_size(self):
        out = dao.Record.query(size=1)
        assert out['hits']['total'] == 2
        assert_equal(len(out['hits']['hits']), 1)

    def test_query_facet(self):
        facet_fields = ['type']
        out = dao.Record.query(facet_fields=facet_fields)
        print pprint.pprint(out)
        facetterms = out['facets']['type']['terms']
        assert len(facetterms) == 2
        assert facetterms[0]['term'] == 'book'
        assert facetterms[0]['count'] == 1

    def test_query_term(self):
        out = dao.Record.query(terms={'type': ['book']})
        assert_equal(out['hits']['total'], 1)


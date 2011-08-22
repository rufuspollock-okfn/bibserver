import os
import json
import pprint
from nose.tools import assert_equal

from test.base import *
from bibserver import dao


class TestDAO:
    @classmethod
    def setup_class(cls):
        pass

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

    def test_query_facet(self):
        facet_fields = ['type']
        out = dao.Record.query(facet_fields=facet_fields)
        print pprint.pprint(out)
        facetterms = out['facets']['type']['terms']
        assert len(facetterms) == 2
        assert facetterms[0]['term'] == 'book'
        assert facetterms[0]['count'] == 1

    def test_query_term(self):
        out = dao.Record.query(terms={'type': 'book'})
        assert_equal(out['hits']['total'], 1)


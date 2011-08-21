import os
import json

from bibserver.config import config
from bibserver import dao

TESTDB = 'bibserver-test'

here = os.path.dirname(__file__)
fixtures_path = os.path.join(here, 'fixtures.json')
fixtures = json.load(open(fixtures_path))

class TestDAO:
    @classmethod
    def setup_class(cls):
        config['ELASTIC_SEARCH_DB'] = TESTDB
        dao.init_db()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_01(self):
        recdict = fixtures['records'][0]
        record = dao.Record.upsert(recdict)
        outrecord = dao.Record.get(record.id)
        for attr in ['type', 'author']:
            assert record[attr] == recdict[attr], record
            assert outrecord[attr] == recdict[attr], outrecord


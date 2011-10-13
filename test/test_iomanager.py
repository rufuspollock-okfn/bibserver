from nose.tools import assert_equal

from test.base import *

import bibserver.iomanager
import bibserver.dao

class TestIOManager:
    @classmethod
    def setup_class(cls):
        recdict = fixtures['records'][0]
        cls.record = dao.Record.upsert(recdict)

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_01(self):
        config = bibserver.config.Config(bibserver.config.config)
        facet_fields = config.facet_fields
        results = bibserver.dao.Record.query('tolstoy',
                facet_fields=facet_fields)
        manager = bibserver.iomanager.IOManager(results)

        assert_equal(manager.numFound(), 1)
        assert_equal(manager.page_size(), 10)

        recorddicts = manager.set()
        print recorddicts
        out = manager.get_str(recorddicts[0], 'title')
        assert recorddicts[0]['title'] in out, out


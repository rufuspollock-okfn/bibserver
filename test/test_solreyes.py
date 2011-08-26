from nose.tools import assert_equal

from test.base import *

import bibserver.solreyes
import bibserver.dao

class TestESResultManager:
    @classmethod
    def setup_class(cls):
        recdict = fixtures['records'][0]
        cls.record = dao.Record.upsert(recdict)

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_01(self):
        config = bibserver.solreyes.Configuration(bibserver.config.config)
        facet_fields = config.get_default_args()['facet_field']
        results = bibserver.dao.Record.query('tolstoy',
                facet_fields=facet_fields)
        args = None
        manager = bibserver.solreyes.ESResultManager(results, config, args)

        assert_equal(manager.numFound(), 1)

        prev = manager.get_previous(0)
        assert_equal(prev, [])

        assert_equal(manager.page_size(), 10)

        out = manager.get_ordered_facets('collection')
        assert_equal(out, [('great',1), ('novels',1)])

        recorddicts = manager.set()
        print recorddicts
        out = manager.get_str(recorddicts[0], 'title')
        assert recorddicts[0]['title'] in out, out


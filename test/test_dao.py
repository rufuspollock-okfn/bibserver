from bibserver.config import config
from bibserver import dao

TESTDB = 'bibserver-test'

class TestDAO:
    @classmethod
    def setup_class(cls):
        config['ELASTIC_SEARCH_DB'] = TESTDB
        dao.init_db()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        # conn.delete_index(TESTDB)

    def test_01(self):
        pass


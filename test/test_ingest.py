from test.base import fixtures, Fixtures, TESTDB
import bibserver.dao as dao
import nose.tools
from bibserver import ingest

class TestIngest:
    @classmethod
    def setup_class(cls):
        Fixtures.create_account()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_ticket_status(self):
        t = dao.IngestTicket.submit(owner='tester', 
                                    collection='test', format='json', source_url='http://127.0.0.1/x')
        assert t['state'] == 'new'
    
    @nose.tools.raises(dao.IngestTicketInvalidInit)
    def test_params(self):
        t = dao.IngestTicket.submit(owner='tester')
        
    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_none(self):
        t = dao.IngestTicket.submit(owner=None, 
                                    collection='test', format='json', source_url='http://127.0.0.1/x')

    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_valid_01(self):
        t = dao.IngestTicket.submit(owner='moocow',
                                    collection='test', format='json', source_url='http://127.0.0.1/x')

    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_valid_02(self):
        t = dao.IngestTicket.submit(owner={}, 
                                    collection='test', format='json', source_url='http://127.0.0.1/x')

#    def test_format(self):
#        assert False
#
#    def test_source_http_or_https(self):
#        assert False
#        
#    def test_valid_collection(self):
#        assert False

    def test_collecting_tickets(self):
        for i in range(10):
            t = dao.IngestTicket.submit(owner='tester', 
                                    collection='test%02.d'%i, format='json', source_url='http://127.0.0.1/x')
        tickets = ingest.get_tickets()
        assert len(tickets) == 10

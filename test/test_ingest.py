from test.base import fixtures, Fixtures, TESTDB
import bibserver.dao as dao
import nose.tools
from bibserver import ingest
from bibserver.config import config
import os

class TestIngest:
    @classmethod
    def setup_class(cls):
        Fixtures.create_account()
        config['download_cache_directory'] = 'test/data/downloads'
        # initialise the plugins
        ingest.init()
        assert 'bibtex' in ingest.PLUGINS

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)
        for x in os.listdir('test/data/downloads'):
            os.unlink(os.path.join('test/data/downloads', x))
        os.rmdir('test/data/downloads')

    @nose.tools.raises(dao.IngestTicketInvalidInit)
    def test_params(self):
        t = dao.IngestTicket.submit(owner='tester')

    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_none(self):
        t = dao.IngestTicket.submit(owner=None, 
                                    collection='test', format='json', source_url='')

    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_valid_01(self):
        t = dao.IngestTicket.submit(owner='moocow',
                                    collection='test', format='json', source_url='')

    @nose.tools.raises(dao.IngestTicketInvalidOwnerException)
    def test_owner_valid_02(self):
        t = dao.IngestTicket.submit(owner={}, 
                                    collection='test', format='json', source_url='')

    def test_download(self):
        URL = 'https://raw.github.com/okfn/bibserver/asyncupload/test/data/sample.bibtex'
        t = dao.IngestTicket.submit(owner='tester', 
                                     collection='test', format='bibtex', source_url=URL)
        assert t['state'] == 'new'
        
        assert len(ingest.get_tickets()) == 1
        
        ingest.determine_action(t)
        assert t['state'] == 'downloaded'
        assert t['data_md5'] == 'b61489f0a0f32a26be4c8cfc24574c0e'

    def test_failed_download(self):
        t = dao.IngestTicket.submit(source_url='bogus_url',
                                    owner='tester', collection='test', format='json', )
        
        ingest.determine_action(t)
        assert t['state'] == 'failed'
        
    def test_get_tickets(self):
        tckts = ingest.get_tickets()
        assert len(tckts) == 2
        for t in tckts:
            assert 'tester/test,' in str(t)

    def test_parse(self):
        t = ingest.get_tickets('downloaded')[0]
        ingest.determine_action(t)
        assert t['state'] == 'parsed'

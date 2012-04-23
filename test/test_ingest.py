from test.base import fixtures, Fixtures, TESTDB
import bibserver.dao as dao
import nose.tools
from bibserver import ingest, dao
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

    @nose.tools.raises(ingest.IngestTicketInvalidInit)
    def test_params(self):
        t = ingest.IngestTicket(owner='tester')

    @nose.tools.raises(ingest.IngestTicketInvalidOwnerException)
    def test_owner_none(self):
        t = ingest.IngestTicket(owner=None, 
                                    collection='test', format='json', source_url='')

    def test_owner_valid_01(self):
        unknown_owner = dao.Account.get('moocow')
        assert unknown_owner is None
        t = ingest.IngestTicket(owner='moocow',
                                    collection='test', format='json', source_url='')

    @nose.tools.raises(ingest.IngestTicketInvalidOwnerException)
    def test_owner_valid_02(self):
        t = ingest.IngestTicket(owner={}, 
                                    collection='test', format='json', source_url='')

    def test_download(self):
        # Note: the URL intentionally has a space at the end
        URL = 'https://raw.github.com/okfn/bibserver/master/test/data/sample.bibtex '
        t = ingest.IngestTicket(owner='tester', 
                                     collection='test', format='bibtex', source_url=URL)
        assert t['state'] == 'new'
        t.save()
        assert len(ingest.get_tickets()) == 1
        
        ingest.determine_action(t)
        assert t['state'] == 'downloaded'
        assert t['data_md5'] == 'b61489f0a0f32a26be4c8cfc24574c0e'

    def test_failed_download(self):
        t = ingest.IngestTicket(source_url='bogus_url',
                                    owner='tester', collection='test', format='json', )
        
        ingest.determine_action(t)
        assert t['state'] == 'failed'
        
    def test_get_tickets(self):
        tckts = ingest.get_tickets()
        assert len(tckts) > 0
        for t in tckts:
            assert 'tester/test,' in str(t)

    def test_parse_and_index(self):
        URL = 'https://raw.github.com/okfn/bibserver/master/test/data/sample.bibtex'
        t = ingest.IngestTicket(owner='tester', 
                                     collection=u'test', format='bibtex', source_url=URL)
        ingest.determine_action(t); print repr(t)
        assert t['state'] == 'downloaded'
        ingest.determine_action(t); print repr(t)
        assert t['state'] == 'parsed'
        ingest.determine_action(t); print repr(t)
        assert t['state'] == 'done'
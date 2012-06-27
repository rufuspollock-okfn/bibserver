from test.base import fixtures, Fixtures, TESTDB
import bibserver.dao as dao
import nose.tools
from bibserver import ingest, dao
from bibserver.config import config
import os, json, subprocess

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
        
        data_path = 'test/data/downloads/' + t['data_json']
        data = json.loads(open(data_path).read())
        assert data['records'][0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'
        
    def test_bibtex_empty_name(self):
        p = ingest.PLUGINS.get('bibtex')
        inp_data = '''@article{srising66,
        author="H. M. Srivastava and ",
        title="{zzz}",
        journal="zzz",
        volume=zzz,
        pages="zzz",
        year=zzz}'''
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = p.communicate(input=inp_data)[0]
        data = json.loads(data)
        assert len(data['records'][0]['author']) == 1
        
    def test_bibtex_utf(self):
        p = ingest.PLUGINS.get('bibtex')
        inp_data = open('test/data/sampleutf8.bibtex').read()
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = p.communicate(input=inp_data)[0]
        data = json.loads(data)
        assert data['records'][0]['title'] == u'\u201cBibliotheken fu\u0308r o\u0308ffnen\u201d'

    def test_bibtex_missing_comma(self):
        inp_data = '''@article{digby_mnpals_2011,
author = {Todd Digby and Stephen Elfstrand},
title = {{Open Source Discovery: Using VuFind to create MnPALS Plus}},
journal = {Computers in Libraries},
year = {2011},
month = {March}
}'''
        p = ingest.PLUGINS.get('bibtex')
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = p.communicate(input=inp_data)[0]
        data = json.loads(data)
        print repr(data['records'][0])
        assert 'month' not in data['records'][0]

    def test_bibtex_keywords(self):
        inp_data = '''@misc{Morgan2011,
            author = {Morgan, J. T. and Geiger, R. S. and Pinchuk, M. and Walker, S.},
            keywords = {open\_access, wrn2011, wrn201107, thing\#withhash},
            title = {{This is a test}},
            year = {2011}
        }
'''
        p = ingest.PLUGINS.get('bibtex')
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = p.communicate(input=inp_data)[0]
        data = json.loads(data)
        assert 'keyword' in data['records'][0]
        assert u'open_access' in data['records'][0].get('keyword'), data['records'][0].get('keyword')
        assert u'thing#withhash' in data['records'][0].get('keyword'), data['records'][0].get('keyword')

    def test_csv(self):
        p = ingest.PLUGINS.get('csv')
        inp_data = open('test/data/sample.csv').read()
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = p.communicate(input=inp_data)[0]
        data = json.loads(data)
        assert data['records'][0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'

    def test_BOM(self):
        csv_file = '''"bibtype","citekey","title","author","year","eprint","subject"
        "misc","arXiv:0807.3308","Visibility to infinity in the hyperbolic plane, despite obstacles","Itai Benjamini,Johan Jonasson,Oded Schramm,Johan Tykesson","2008","arXiv:0807.3308","sle"        
'''
        csv_file_with_BOM = '\xef\xbb\xbf' + csv_file
        p = ingest.PLUGINS.get('csv')
        pp = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data1 = json.loads(pp.communicate(input=csv_file)[0])
        pp = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data2 = json.loads(pp.communicate(input=csv_file_with_BOM)[0])

        assert data1['records'][0]['bibtype'] == data2['records'][0]['bibtype']

#
    def test_risparser_01(self):
        inp_data = open('test/data/sample.ris').read()
        p = ingest.PLUGINS.get('ris')
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = json.loads(p.communicate(input=inp_data)[0])
        data = data['records']
        assert len(data) == 240
        assert type(data[0]['title']) is unicode
        assert data[0]['title'] == u'Using Workflows to Explore and Optimise Named Entity Recognition for Chemisty'
        assert len(data[0]['author']) == 5
        data[0]['author'][0] = {'name': u'Kolluru, B.K.'}
        
    def test_risparser_runon_lines(self):
        inp_data = '''TY  - JOUR
AU  - Murray-Rust, P.
JF  - Org. Lett.
TI  - [Red-breasted 
  goose 
  colonies]
PG  - 559-68
'''
        p = ingest.PLUGINS.get('ris')
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = json.loads(p.communicate(input=inp_data)[0])
        data = data['records']
        assert data[0]['title'] == u'[Red-breasted goose colonies]'

    def test_json_01(self):
        inp_data = '''
{
    "records": [
        {
            "Comment": "haven't yet found an example of gratisOA beyond PMC deposition http://www.ncbi.nlm.nih.gov/pmc/?term=science%5Bjournal%5D", 
            "Publisher": "AAAS", 
            "links": [], 
            "Reporter": "Ross", 
            "Some Journals": "Science", 
            "Brand (if any)": "", 
            "link to oldest": "", 
            "cid": "2", 
            "Licence": "", 
            "title": "AAAS: Science", 
            "Number of articles affected": "", 
            "oldest gratis OA": ""
        }
]}
'''
        p = ingest.PLUGINS.get('json')
        p = subprocess.Popen(p['_path'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = json.loads(p.communicate(input=inp_data)[0])
        data = data['records']
        assert data[0]['title'] == u'AAAS: Science'

    def test_plugin_dump(self):
        plugins = ingest.get_plugins()
        assert len(plugins.keys()) > 0

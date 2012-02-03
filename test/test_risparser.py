from bibserver.parsers.RISParser import RISParser
from cStringIO import StringIO

class TestRISParser:
    def test_01(self):
        collection = 'testing'
        sample = open('test/data/sample.ris')
        parser = RISParser(sample)
        data, metadata = parser.parse()
        assert len(data) == 240
        assert type(data[0]['title']) is unicode
        assert data[0]['title'] == u'Using Workflows to Explore and Optimise Named Entity Recognition for Chemisty'
        assert len(data[0]['author']) == 5
        data[0]['author'][0] = {'name': u'Kolluru, B.K.'}
        
    def test_runon_lines(self):
        collection = 'testing'
        sample = StringIO('''TY  - JOUR
AU  - Murray-Rust, P.
JF  - Org. Lett.
TI  - [Red-breasted 
  goose 
  colonies]
PG  - 559-68
''')
        parser = RISParser(sample)
        data, metadata = parser.parse()
        print data[0]
        assert data[0]['title'] == u'[Red-breasted goose colonies]'
        
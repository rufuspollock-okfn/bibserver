from bibserver.parsers.RISParser import RISParser

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
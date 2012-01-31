from bibserver.parsers.BibTexParser import BibTexParser

class TestBibTexParser:
    def test_01(self):
        collection = 'testing'
        sample = open('test/data/sample.bibtex')
        parser = BibTexParser(sample)
        data, metadata = parser.parse()
        print data
        assert data[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'

    def test_empty_name(self):
        collection = 'testing'
        sample = open('test/data/sampleutf8.bibtex')
        parser = BibTexParser(sample)
        data, metadata = parser.parse()
        print data[0]['title']
        assert data[0]['title'] == u'\u201cBibliotheken fu\u0308r o\u0308ffnen\u201d'


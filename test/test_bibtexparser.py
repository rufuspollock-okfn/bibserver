from bibserver.parsers.BibTexParser import BibTexParser

class TestBibTexParser:
    def test_01(self):
        collection = 'testing'
        sample = open('test/data/sample.bibtex')
        parser = BibTexParser(sample)
        data, metadata = parser.parse()
        print data
        assert data[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'


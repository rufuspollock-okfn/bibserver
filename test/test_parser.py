import bibserver.parser

class TestParser:
    def test_01(self):
        bibtex = open('test/data/sample.bibtex')
        ds = bibserver.parser.Parser()
        data, metadata = ds.parse(bibtex, 'bibtex')
        assert data[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'


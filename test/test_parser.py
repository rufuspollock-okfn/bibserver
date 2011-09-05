import bibserver.parser

class TestParser:
    def test_01(self):
        bibtex = open('test/data/sample.bibtex')
        ds = bibserver.parser.Parser()
        out = ds.parse(bibtex, 'bibtex')
        assert out[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'


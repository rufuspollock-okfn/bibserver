import bibserver.parser

class TestParser:
    def test_01(self):
        bibtex = open('test/data/sample.bibtex')
        ds = bibserver.parser.Parser()
        data, metadata = ds.parse(bibtex, 'bibtex')
        assert data[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'

    def test_BOM(self):
        from cStringIO import StringIO
        csv_file = '''"bibtype","citekey","title","author","year","eprint","subject"
        "misc","arXiv:0807.3308","Visibility to infinity in the hyperbolic plane, despite obstacles","Itai Benjamini,Johan Jonasson,Oded Schramm,Johan Tykesson","2008","arXiv:0807.3308","sle"        
'''
        csv_file_with_BOM = '\xef\xbb\xbf' + csv_file
        ds = bibserver.parser.Parser()
        data1, metadata = ds.parse(StringIO(csv_file), 'csv')
        data2, metadata = ds.parse(StringIO(csv_file_with_BOM), 'csv')
        assert data1[0]['bibtype'] == data2[0]['bibtype']
        
        
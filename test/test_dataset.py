import bibserver.dataset 

class TestDataset:
    def test_01(self):
        collection = 'testing'
        bibtex = open('test/data/sample.bibtex')
        ds = bibserver.dataset.DataSet()
        out = ds.convert(bibtex, 'bibtex', collection)
        assert out[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'


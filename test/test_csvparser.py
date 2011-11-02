from bibserver.parsers.CSVParser import CSVParser

class TestCSVParser:
    def test_01(self):
        collection = 'testing'
        sample = open('test/data/sample.csv')
        parser = CSVParser()
        data, metadata = parser.parse(sample)
        assert data[0]['title'] == 'Visibility to infinity in the hyperbolic plane, despite obstacles'


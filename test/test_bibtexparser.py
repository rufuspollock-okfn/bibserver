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
        from cStringIO import StringIO
        collection = 'testing'
        parser = BibTexParser(StringIO('''@article{srising66,
        author="H. M. Srivastava and ",
        title="{zzz}",
        journal="zzz",
        volume=zzz,
        pages="zzz",
        year=zzz}'''))
        data, metadata = parser.parse()

    def test_utf(self):
        collection = 'testing'
        sample = open('test/data/sampleutf8.bibtex')
        parser = BibTexParser(sample)
        data, metadata = parser.parse()
        print data[0]['title']
        assert data[0]['title'] == u'\u201cBibliotheken fu\u0308r o\u0308ffnen\u201d'

    def test_missing_comma(self):
        from cStringIO import StringIO
        collection = 'testing'
        parser = BibTexParser(StringIO('''@article{digby_mnpals_2011,
author = {Todd Digby and Stephen Elfstrand},
title = {{Open Source Discovery: Using VuFind to create MnPALS Plus}},
journal = {Computers in Libraries},
year = {2011},
month = {March}
}'''))
        data, metadata = parser.parse()
        print data
        assert 'month' in data[0]
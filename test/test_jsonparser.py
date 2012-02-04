from bibserver.parsers.JSONParser import JSONParser
from cStringIO import StringIO

class TestJSONParser:        
    def test_01(self):
        collection = 'testing'
        sample = StringIO('''
{
    "records": [
        {
            "Comment": "haven't yet found an example of gratisOA beyond PMC deposition http://www.ncbi.nlm.nih.gov/pmc/?term=science%5Bjournal%5D", 
            "Publisher": "AAAS", 
            "links": [], 
            "Reporter": "Ross", 
            "Some Journals": "Science", 
            "Brand (if any)": "", 
            "link to oldest": "", 
            "cid": "2", 
            "Licence": "", 
            "title": "AAAS: Science", 
            "Number of articles affected": "", 
            "oldest gratis OA": ""
        }
]}
''')
        parser = JSONParser(sample)
        data, metadata = parser.parse()
        print data[0]
        assert data[0]['title'] == u'AAAS: Science'
        
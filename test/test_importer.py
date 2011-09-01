from base import *

from bibserver.importer import Importer
import bibserver.dao
import os

class TestImporter:
    def test_upload(self):
        i = Importer()
        bibtex = open('test/data/sample.bibtex').read()
        pkg = {
            'format': 'bibtex',
            'data': bibtex
            }
        records = i.upload(pkg)
        recid = records[0]['id']
        out = bibserver.dao.Record.get(recid)
        assert out['year'] == '2008', out
'''
    def test_bulkupload(self):
        i = Importer()
        toupload = json.load('test/data/bulk_import.json')
        
        # fix upload collection relative to test
        toupload["collections"][0]["source"] = fixtures_path = os.path.join(os.path.dirname(__file__), '/data/', toupload["collections"][0]["source"])
        toupload["collections"][1]["source"] = fixtures_path = os.path.join(os.path.dirname(__file__), '/data/', toupload["collections"][1]["source"])

        # do the bulk upload
        records = i.bulk_upload(toupload)
        recid = records[0]['id']
        out = bibserver.dao.Record.get(recid)
        assert out['year'] == '2008', out
'''

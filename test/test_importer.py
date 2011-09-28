from base import *

from bibserver.importer import Importer
import bibserver.dao
import os

class TestImporter:
    @classmethod
    def setup_class(cls):
        cls.owner = dao.Account(id='testaccount')
        cls.owner.save()

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_upload(self):
        i = Importer(owner=self.owner)
        bibtex = open('test/data/sample.bibtex').read()
        pkg = {
            'format': 'bibtex',
            'data': bibtex
            }
        records = i.upload(pkg)
        recid = records[1]['id']
        out = bibserver.dao.Record.get(recid)
        assert out["year"] == '2008', out

    def test_bulkupload(self):
        i = Importer(owner=self.owner)
        colls = open('test/data/bulk_upload.json').read()
        toupload = json.loads(colls)
        
        # fix upload collection relative to test
        toupload["collections"][0]["source"] = 'file://' + os.path.join(os.path.dirname(__file__), toupload["collections"][0]["source"])
        toupload["collections"][1]["source"] = 'file://' + os.path.join(os.path.dirname(__file__), toupload["collections"][1]["source"])

        # do the bulk upload
        records = i.bulk_upload(toupload)
        assert records == True, records


from base import *

from bibserver.importer import Importer
import bibserver.dao
import os

class TestImporter:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        conn, db = dao.get_conn()
        conn.delete_index(TESTDB)

    def test_upload(self):
        owner = dao.Account(id='testaccount1')
        owner.save()
        i = Importer(owner=owner)
        bibtex = open('test/data/sample.bibtex')
        format_ = 'bibtex'
        collection_in = {
            'label': u'My Test Collection'
            }
        coll, records = i.upload(bibtex, format_, collection_in)
        assert coll.id
        assert owner.collections[0].id == coll.id, owner.collections

        assert len(records) == 1, records
        recid = records[0]['id']
        out = bibserver.dao.Record.get(recid)
        assert out["year"] == '2008', out
        assert out['collection'][0] == coll['id']

        # now try uploading exactly the same data again
        bibtex = open('test/data/sample.bibtex')
        original_coll_id = coll.id
        newcoll, records = i.upload(bibtex, format_, collection_in)
        # still should have only one collection
        assert len(owner.collections) == 1
        assert newcoll.id == original_coll_id
        assert len(records) == 1
        assert records[0]['collection'][0] == original_coll_id
        # still should have only one record in it
        recs_for_collection = dao.Record.query(terms={
            'collection': [coll.id]
            })
        assert recs_for_collection['hits']['total'] == 1, recs_for_collection

    def test_bulkupload(self):
        owner = dao.Account(id='testaccount2')
        owner.save()
        i = Importer(owner=owner)
        colls = open('test/data/bulk_upload.json').read()
        toupload = json.loads(colls)
        
        # fix upload collection relative to test
        toupload["collections"][0]["source"] = 'file://' + os.path.join(os.path.dirname(__file__), toupload["collections"][0]["source"])
        toupload["collections"][1]["source"] = 'file://' + os.path.join(os.path.dirname(__file__), toupload["collections"][1]["source"])

        # TODO: a better test
        # do the bulk upload
        records = i.bulk_upload(toupload)
        assert records == True, records


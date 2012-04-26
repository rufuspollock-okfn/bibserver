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
        data = open('test/data/sample.bibtex.bibjson')
        collection_in = {
            'label': u'My Test Collection'
            }
        coll, records = i.upload(data, collection_in)
        assert coll.id
        assert owner.collections[0].id == coll.id, owner.collections

        assert len(records) == 1, records
        recid = records[0]['_id']
        out = bibserver.dao.Record.get(recid)
        assert out["year"] == '2008', out
        assert out['collection'] == coll['collection']

        # now try uploading exactly the same data again
        data = open('test/data/sample.bibtex.bibjson')
        newcoll, records = i.upload(data, collection_in)
        # still should have only one collection
        assert len(owner.collections) == 1
        assert newcoll.id == coll.id
        assert len(records) == 1
        assert records[0]['collection'] == coll['collection']
        # still should have only one record in it
        recs_for_collection = dao.Record.query('collection:"' + coll['collection'] + '"')
        assert recs_for_collection['hits']['total'] == 1, recs_for_collection


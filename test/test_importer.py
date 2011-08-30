from base import *

from bibserver.importer import Importer
import bibserver.dao


class TestImporter:
    def test_schedule(self):
        m = Importer()
        bibtex = open('test/data/sample.bibtex').read()
        pkg = {
            'format': 'bibtex',
            'data': bibtex
            }
        records = m.upload(pkg)
        recid = records[0]['id']
        out = bibserver.dao.Record.get(recid)
        assert out['year'] == '2008', out


from base import *

from bibserver.manager import Manager
import bibserver.dao


class TestManager:
    def test_schedule(self):
        m = Manager()
        bibtex = open('test/data/sample.bibtex').read()
        pkg = {
            'format': 'bibtex',
            'data': bibtex
            }
        records = m.schedule(pkg)
        recid = records[0]['id']
        out = bibserver.dao.Record.get(recid)
        assert out['year'] == '2008', out


import os
import json

from bibserver.config import config
from bibserver import dao

TESTDB = 'bibserver-test'

here = os.path.dirname(__file__)
fixtures_path = os.path.join(here, 'fixtures.json')
fixtures = json.load(open(fixtures_path))

config['ELASTIC_SEARCH_DB'] = TESTDB
dao.init_db()

__all__ = ['config', 'fixtures', 'dao', 'TESTDB']


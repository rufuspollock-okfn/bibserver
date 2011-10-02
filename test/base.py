import os
import json

from bibserver import dao
from bibserver.config import config

TESTDB = 'bibserver-test'

here = os.path.dirname(__file__)
fixtures_path = os.path.join(here, 'fixtures.json')
fixtures = json.load(open(fixtures_path))

config["ELASTIC_SEARCH_DB"] = TESTDB
dao.init_db()


class Fixtures(object):
    raw = fixtures

    @classmethod
    def create_account(cls):
        accountdict = dict(fixtures['accounts'][0])
        pw = accountdict['password_raw']
        del accountdict['password_raw']
        cls.account = dao.Account(**accountdict)
        cls.account.set_password(pw)
        cls.account.save()

__all__ = ['config', 'fixtures', 'Fixtures', 'dao', 'TESTDB', 'json']


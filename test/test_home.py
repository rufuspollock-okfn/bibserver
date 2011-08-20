from bibserver import web


class TestHome(object):
    @classmethod
    def setup_class(cls):
        web.app.config['TESTING'] = True
        cls.app = web.app.test_client()

    def test_home(self):
        res = self.app.get('/')
        assert 'BibSoup' in res.data, res.data


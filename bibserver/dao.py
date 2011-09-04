# this is the data access layer
import json
import uuid
import UserDict
import httplib

import pyes

from bibserver.config import config

def init_db():
    conn, db = get_conn()
    try:
        conn.create_index(db)
    except pyes.exceptions.IndexAlreadyExistsException:
        pass

def get_conn():
    host = str(config['ELASTIC_SEARCH_HOST'])
    db_name = config['ELASTIC_SEARCH_DB']
    conn = pyes.ES([host])
    return conn, db_name


class DomainObject(UserDict.IterableUserDict):
    # set __type__ on inheriting class to determine elasticsearch object
    __type__ = None

    def __init__(self, **kwargs):
        '''Initialize a domain object with key/value pairs of attributes.
        '''
        # IterableUserDict expects internal dictionary to be on data attribute
        self.data = dict(kwargs)

    @property
    def id(self):
        '''Get id of this object.'''
        return self.data.get('id', None)

    def save(self):
        '''Save to backend storage.'''
        # TODO: refresh object with result of save
        return self.upsert(self.data)

    @classmethod
    def get(cls, id_):
        '''Retrieve object by id.'''
        conn, db = get_conn()
        try:
            out = conn.get(db, cls.__type__, id_)
            return cls(**out['_source'])
        except pyes.exceptions.ElasticSearchException, inst:
            if inst.status == 404:
                return None
            else:
                raise

    @classmethod
    def upsert(cls, data, state=None):
        '''Update backend object with a dictionary of data.

        If no id is supplied an uuid id will be created before saving.
        '''
        conn, db = get_conn()
        if 'id' in data:
            id_ = data['id']
        else:
            id_ = uuid.uuid4().hex
            data['id'] = id_
        conn.index(data, db, cls.__type__, id_)
        # TODO: ES >= 0.17 automatically re-indexes on GET so this not needed
        conn.refresh()
        # TODO: should we really do a cls.get() ?
        return cls(**data)

    @classmethod
    def bulk_upsert(cls, dataset, state=None):
        '''Bulk update backend object with a list of dicts of data.

        If no id is supplied an uuid id will be created before saving.
        '''
        try:
            conn, db = get_conn()
            for data in dataset:
                if 'id' in data:
                    id_ = data['id']
                else:
                    id_ = uuid.uuid4().hex
                    data['id'] = id_
                conn.index(data, db, cls.__type__, id_, bulk=True)
            # refresh required after bulk index
            conn.refresh()
            return dataset
        except:
            return False
    
    @classmethod
    def query(cls, q='', terms=None, facet_fields=None, **kwargs):
        '''Perform a query on backend.

        :param q: maps to query_string parameter.
        :param terms: dictionary of terms to filter on. values should be lists.
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        '''
        conn, db = get_conn()
        if not q:
            ourq = pyes.query.MatchAllQuery()
        else:
            ourq = pyes.query.StringQuery(q, default_operator='AND')
        if terms:
            for term in terms:
                termq = pyes.query.TermQuery(term, terms[term])
                ourq = pyes.query.BoolQuery(must=[ourq,termq])
        ourq = ourq.search(**kwargs)
        if facet_fields:
            for field in facet_fields:
                ourq.facet.add_term_facet(field)
        out = conn.search(ourq, db, cls.__type__)
        return out

    @classmethod
    def raw_query(self, query_string):
        if not query_string:
            msg = json.dumps({
                'error': "Query endpoint. Please provide elastic search <a href='%s'>query parameters.</a>" % (
                    'http://www.elasticsearch.org/guide/reference/api/search/uri-request.html'
                )})
            return msg

        host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
        db_name = config['ELASTIC_SEARCH_DB']
        fullpath = '/' + db_name + '/' + self.__type__ + '/_search' + '?' + query_string
        c =  httplib.HTTPConnection(host)
        c.request('GET', fullpath)
        result = c.getresponse()
        # pass through the result raw
        return result.read()


class Record(DomainObject):
    __type__ = 'record'




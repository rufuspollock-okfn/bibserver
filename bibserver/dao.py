# this is the data access layer
import json
import uuid
import UserDict
import httplib
import urllib
from datetime import datetime

import pyes
from werkzeug import generate_password_hash, check_password_hash
from flaskext.login import UserMixin

from bibserver.config import config
import bibserver.util

def init_db():
    conn, db = get_conn()
    try:
        conn.create_index(db)
    except pyes.exceptions.IndexAlreadyExistsException:
        pass
    mappings = config["mappings"]
    for mapping in mappings:
        host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
        db_name = config['ELASTIC_SEARCH_DB']
        fullpath = '/' + db_name + '/' + mapping + '/_mapping'
        c =  httplib.HTTPConnection(host)
        c.request('GET', fullpath)
        result = c.getresponse()
        if result.status == 404:
            c =  httplib.HTTPConnection(host)
            c.request('PUT', fullpath, json.dumps(mappings[mapping]))
            c.getresponse()


def get_conn():
    host = str(config["ELASTIC_SEARCH_HOST"])
    db_name = config["ELASTIC_SEARCH_DB"]
    conn = pyes.ES([host])
    if "default_indices" in config:
        if isinstance(config["default_indices"],list) and len(config["default_indices"]) > 0:
            conn.default_indices = config["default_indices"]
    return conn, db_name

class InvalidDAOIDException(Exception):
    pass
    
class DomainObject(UserDict.IterableUserDict):
    # set __type__ on inheriting class to determine elasticsearch object
    __type__ = None

    def __init__(self, **kwargs):
        '''Initialize a domain object with key/value pairs of attributes.
        '''
        # IterableUserDict expects internal dictionary to be on data attribute
        if '_source' in kwargs:
            self.data = dict(kwargs['_source'])
            self.meta = dict(kwargs)
            del self.meta['_source']
        else:
            self.data = dict(kwargs)

    @property
    def id(self):
        '''Get id of this object.'''
        return self.data.get('id', None)
        
    @property
    def version(self):
        return self.meta.get('_version', None)

    def save(self):
        '''Save to backend storage.'''
        # TODO: refresh object with result of save
        return self.upsert(self.data)

    @classmethod
    def get(cls, id_):
        '''Retrieve object by id.'''
        if id_ is None:
            return None
        conn, db = get_conn()
        try:
            out = conn.get(db, cls.__type__, id_)
            return cls(**out)
        except pyes.exceptions.ElasticSearchException, inst:
            if inst.status == 404:
                return None
            else:
                raise

    @classmethod
    def get_mapping(cls):
        conn, db = get_conn()
        return conn.get_mapping(cls.__type__, db)

    @classmethod
    def upsert(cls, data, state=None):
        '''Update backend object with a dictionary of data.

        If no id is supplied an uuid id will be created before saving.
        '''
        conn, db = get_conn()
        cls.bulk_upsert([data], state)
        conn.flush_bulk()

        # TODO: should we really do a cls.get() ?
        return cls(**data)

    @classmethod
    def bulk_upsert(cls, dataset, state=None):
        '''Bulk update backend object with a list of dicts of data.
        If no id is supplied an uuid id will be created before saving.'''
        conn, db = get_conn()
        for data in dataset:
            if 'id' in data:
                id_ = data['id']
            else:
                id_ = uuid.uuid4().hex
                data['id'] = id_
            
            if '_created' not in data:
                data['_created'] = datetime.now().isoformat()
            data['_last_modified'] = datetime.now().isoformat()
            
            # TODO: as owner is now required per record, should perhaps insert a check for owner here
            conn.index(data, db, cls.__type__, urllib.quote_plus(id_), bulk=True)
        # refresh required after bulk index
        conn.refresh()
        return dataset
    
    @classmethod
    def delete_by_query(cls, query):
        url = str(config['ELASTIC_SEARCH_HOST'])
        loc = config['ELASTIC_SEARCH_DB'] + "/" + cls.__type__ + "/_query?q=" + urllib.quote_plus(query)
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        return resp.read()
        
    @classmethod
    def query(cls, q='', terms=None, facet_fields=None, flt=False, default_operator='AND', **kwargs):
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
            if flt:
                ourq = pyes.query.FuzzyLikeThisQuery(like_text=q,**kwargs)
            else:
                ourq = pyes.query.StringQuery(q, default_operator=default_operator)
        if terms:
            for term in terms:
                if isinstance(terms[term],list):
                    for val in terms[term]:
                        termq = pyes.query.TermQuery(term, val)
                        ourq = pyes.query.BoolQuery(must=[ourq,termq])
                else:
                    termq = pyes.query.TermQuery(term, terms[term])
                    ourq = pyes.query.BoolQuery(must=[ourq,termq])

        ourq = ourq.search(**kwargs)
        if facet_fields:
            for item in facet_fields:
                ourq.facet.add_term_facet(item['key'], size=item.get('size',100), order=item.get('order',"count"))
        out = conn.search(ourq, db, cls.__type__)
        return out

    @classmethod
    def raw_query(self, query_string):
        if not query_string:
            msg = json.dumps({
                'error': "Query endpoint. Please provide elastic search query parameters - see http://www.elasticsearch.org/guide/reference/api/search/uri-request.html"
                })
            return msg

        host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
        db_path = config['ELASTIC_SEARCH_DB']
        fullpath = '/' + db_path + '/' + self.__type__ + '/_search' + '?' + query_string
        c =  httplib.HTTPConnection(host)
        c.request('GET', fullpath)
        result = c.getresponse()
        # pass through the result raw
        return result.read()


class Record(DomainObject):
    __type__ = 'record'


class Collection(DomainObject):
    __type__ = 'collection'
    
    def __len__(self):
        res = Record.query(terms={'owner':self['owner'],'collection':self['collection']})
        return res['hits']['total']
    
class Account(DomainObject, UserMixin):
    __type__ = 'account'

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def collections(self):
        colls = Collection.query(terms={
            'owner': [self.id]
            })
        colls = [ Collection(**item['_source']) for item in colls['hits']['hits'] ]
        return colls

class IngestTicketInvalidOwnerException(Exception):
    pass
class IngestTicketInvalidInit(Exception):
    pass
    
class IngestTicket(DomainObject):
    __type__ = 'ingestticket'
    state_choices = ['new', 'downloading', 'downloaded', 'failed', 'populating_index', 'done']
        
    @classmethod
    def submit(cls, **kwargs ):
        'Creates a new Ingest Ticket, ready for processing by the ingest pipeline'
        owner = kwargs.get('owner')
        if not type(owner) in (str, unicode):
            raise IngestTicketInvalidOwnerException()
        owner_obj = Account.get(owner)
        if owner_obj is None:
            raise IngestTicketInvalidOwnerException()
        kwargs['state'] = 'new'
        for x in ('collection', 'format', 'source_url'):
            if not kwargs.get(x):
                raise IngestTicketInvalidInit('You need to supply the parameter %s' % x)
        return cls.upsert(kwargs)

    def __unicode__(self):
        return u'%s/%s [%s] - %s' % (self['owner'], self['collection'], self['state'], self['_last_modified'])
        
    def __str__(self):
        return unicode(self).encode('utf8')
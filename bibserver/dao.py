# this is the data access layer
import json
import uuid
import UserDict
import httplib
import urllib
from datetime import datetime
import hashlib

import pyes
from werkzeug import generate_password_hash, check_password_hash
from flask_login import UserMixin

from bibserver.config import config
import bibserver.util, bibserver.auth


def make_id(data):
    '''Create a new id for data object based on a hash of the data representation
    Ignore the _last_modified, _created fields
    ##TODO Ignore ALL fields that startswith _
    '''
    if '_id' in data: return data['_id']
    new_data = {}
    for k,v in data.items():
        if k in ('_last_modified', '_created'): continue
        new_data[k] = v
    buf = json.dumps(new_data, sort_keys=True)
    new_id = hashlib.md5(buf).hexdigest()
    return new_id
    
    
def init_db():
    conn, db = get_conn()
    try:
        conn.create_index(db)
    except:
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
            print mapping
            c =  httplib.HTTPConnection(host)
            c.request('PUT', fullpath, json.dumps(mappings[mapping]))
            res = c.getresponse()
            print res.read()


def get_conn():
    host = str(config["ELASTIC_SEARCH_HOST"])
    db_name = config["ELASTIC_SEARCH_DB"]
    conn = pyes.ES([host])
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
        return self.data.get('_id', None)
        
    @property
    def version(self):
        return self.meta.get('_version', None)

    def save(self):
        '''Save to backend storage.'''
        # TODO: refresh object with result of save
        return self.upsert(self.data)

    def delete(self):
        url = str(config['ELASTIC_SEARCH_HOST'])
        loc = config['ELASTIC_SEARCH_DB'] + "/" + self.__type__ + "/" + self.id
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        return ''

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
    def get_facets_from_mapping(cls,mapping=False,prefix=''):
        # return a sorted list of all the keys in the index
        if not mapping:
            mapping = cls.get_mapping()[cls.__type__]['properties']
        keys = []
        for item in mapping:
            if mapping[item].has_key('fields'):
                for item in mapping[item]['fields'].keys():
                    if item != 'exact' and not item.startswith('_'):
                        keys.append(prefix + item + config['facet_field'])
            else:
                keys = keys + cls.get_facets_from_mapping(mapping=mapping[item]['properties'],prefix=prefix+item+'.')
        keys.sort()
        return keys
        
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
            if not type(data) is dict: continue
            if '_id' in data:
                id_ = data['_id'].strip()
            else:
                id_ = make_id(data)
                data['_id'] = id_
            
            if '_created' not in data:
                data['_created'] = datetime.now().strftime("%Y%m%d%H%M%S")
            data['_last_modified'] = datetime.now().strftime("%Y%m%d%H%M%S")
            
            index_result = conn.index(data, db, cls.__type__, urllib.quote_plus(id_), bulk=True)
        # refresh required after bulk index
        conn.refresh()
    
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
        host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
        db_path = config['ELASTIC_SEARCH_DB']
        fullpath = '/' + db_path + '/' + self.__type__ + '/_search' + '?' + query_string
        c = httplib.HTTPConnection(host)
        c.request('GET', fullpath)
        result = c.getresponse()
        # pass through the result raw
        return result.read()


class Record(DomainObject):
    __type__ = 'record'


class Note(DomainObject):
    __type__ = 'note'

    @classmethod
    def about(cls, id_):
        '''Retrieve notes by id of record they are about'''
        if id_ is None:
            return None
        conn, db = get_conn()
        res = Note.query(terms={"about":id_})
        return [i['_source'] for i in res['hits']['hits']]


class Collection(DomainObject):
    __type__ = 'collection'

    @property
    def records(self):
        size = Record.query(terms={'owner':self['owner'],'collection':self['collection']})['hits']['total']
        if size != 0:
            res = [Record.get(i['_source']['_id']) for i in Record.query(terms={'owner':self['owner'],'collection':self['collection']},size=size)['hits']['hits']]
        else: res = []
        return res

    @classmethod
    def get_by_owner_coll(cls,owner,coll):
        res = cls.query(terms={'owner':owner,'collection':coll})
        if res['hits']['total'] == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None
            
    def delete(self):
        url = str(config['ELASTIC_SEARCH_HOST'])
        loc = config['ELASTIC_SEARCH_DB'] + "/" + self.__type__ + "/" + self.id
        print loc
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        print resp.read()
        for record in self.records:
            record.delete()
    
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
    def is_super(self):
        return bibserver.auth.user.is_super(self)
    
    @property
    def collections(self):
        colls = Collection.query(terms={
            'owner': [self.id]
            })
        colls = [ Collection(**item['_source']) for item in colls['hits']['hits'] ]
        return colls
        
    @property
    def notes(self):
        res = Note.query(terms={
            'owner': [self.id]
        })
        allnotes = [ Note(**item['_source']) for item in res['hits']['hits'] ]
        return allnotes
        
    def delete(self):
        url = str(config['ELASTIC_SEARCH_HOST'])
        loc = config['ELASTIC_SEARCH_DB'] + "/" + self.__type__ + "/" + self.id
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        for coll in self.collections:
            coll.delete()
        for note in self.notes:
            note.delete()


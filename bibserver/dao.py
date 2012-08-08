# this is the data access layer
import json, UserDict, requests, uuid
from datetime import datetime
import hashlib

from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

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
    mappings = config["mappings"]
    for mapping in mappings:
        t = 'http://' + str(config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/')
        t += '/' + config['ELASTIC_SEARCH_DB'] + '/' + mapping + '/_mapping'
        r = requests.get(t)
        if r.status_code == 404:
            r = requests.put(t, data=json.dumps(mappings[mapping]) )
            print r.text


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

    @classmethod
    def target(cls):
        t = 'http://' + str(config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/') + '/'
        t += config['ELASTIC_SEARCH_DB'] + '/' + cls.__type__ + '/'
        return t

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
        r = requests.delete( self.target + self.id )

    @classmethod
    def get(cls, id_):
        '''Retrieve object by id.'''
        if id_ is None:
            return None
        try:
            out = requests.get(cls.target() + id_)
            if out.status_code == 404:
                return None
            else:
                return cls(**out.json)
        except:
            return None

    @classmethod
    def get_facets_from_mapping(cls,mapping=False,prefix=''):
        # return a sorted list of all the keys in the index
        if not mapping:
            mapping = cls.query(endpoint='_mapping')[cls.__type__]['properties']
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
        cls.bulk_upsert([data], state)

        # TODO: should we really do a cls.get() ?
        return cls(**data)

    @classmethod
    def bulk_upsert(cls, dataset, state=None):
        '''Bulk update backend object with a list of dicts of data.
        If no id is supplied an uuid id will be created before saving.'''
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
            
            r = requests.post(self.target() + self.data['id'], data=json.dumps(self.data))
    
    @classmethod
    def delete_by_query(cls, query):
        r = requests.delete(self.target() + "_query?q=" + query)
        return r.json

    @classmethod
    def query(cls, recid='', endpoint='_search', q='', terms=None, facets=None, **kwargs):
        '''Perform a query on backend.

        :param recid: needed if endpoint is about a record, e.g. mlt
        :param endpoint: default is _search, but could be _mapping, _mlt, _flt etc.
        :param q: maps to query_string parameter if string, or query dict if dict.
        :param terms: dictionary of terms to filter on. values should be lists. 
        :param facets: dict of facets to return from the query.
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        '''
        if recid and not recid.endswith('/'): recid += '/'
        if isinstance(q,dict):
            query = q
        elif q:
            query = {'query': {'query_string': { 'query': q }}}
        else: 
            query = {'query': {'match_all': {}}}

        if facets:
            query['facets'] = {}
            for item in facet_fields:
                query['facets'][item['key']] = {"terms":item}

        if terms:
            boolean = {'must': [] }
            for term in terms:
                if not isinstance(terms[term],list): terms[term] = [terms[term]]
                for val in terms[term]:
                    obj = {'term': {}}
                    obj['term'][ term ] = val
                    boolean['must'].append(obj)
            if q and not isinstance(q,dict): boolean['must'].append( {'query_string': { 'query': q } } )
            query['query'] = {'bool': boolean}

        for k,v in kwargs.items():
            query[k] = v

        if endpoint in ['_mapping']:
            r = requests.get(cls.target() + recid + endpoint)
        else:
            r = requests.post(cls.target() + recid + endpoint, data=json.dumps(query))
        return r.json


class Record(DomainObject):
    __type__ = 'record'


class Note(DomainObject):
    __type__ = 'note'

    @classmethod
    def about(cls, id_):
        '''Retrieve notes by id of record they are about'''
        if id_ is None:
            return None
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
        r = requests.delete( self.target + self.id )
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
        r = requests.delete( self.target + self.id )
        for coll in self.collections:
            coll.delete()
        for note in self.notes:
            note.delete()


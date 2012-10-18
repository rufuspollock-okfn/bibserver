# this is the data access layer
import json, UserDict, requests, uuid
from datetime import datetime
import hashlib

from bibserver.core import app, current_user

from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

import bibserver.util as util
import bibserver.auth
    
    
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
            self.meta = {}
            self.data = dict(kwargs)

    @classmethod
    def target(cls):
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/' + cls.__type__ + '/'
        return t

    @property
    def id(self):
        '''Get id of this object.'''
        return self.data.get('_id', None)
        
    @property
    def version(self):
        return self.meta.get('_version', None)

    @property
    def json(self):
        return json.dumps(self.data)
        
    def save(self):
        if not self.id: self.data['_id'] = uuid.uuid4().hex
        if '_created' not in self.data:
            self.data['_created'] = datetime.now().strftime("%Y-%m-%d %H%M")
        self.data['_last_modified'] = datetime.now().strftime("%Y-%m-%d %H%M")
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))

    def delete(self):
        r = requests.delete( self.target() + self.id )

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
                        keys.append(prefix + item + app.config['facet_field'])
            else:
                keys = keys + cls.get_facets_from_mapping(mapping=mapping[item]['properties'],prefix=prefix+item+'.')
        keys.sort()
        return keys
            
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
            if 'facets' not in query:
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
            if q and not isinstance(q,dict):
                boolean['must'].append( {'query_string': { 'query': q } } )
            elif q and 'query' in q:
                boolean['must'].append( query['query'] )
            query['query'] = {'bool': boolean}

        for k,v in kwargs.items():
            if k == '_from':
                query['from'] = v
            else:
                query[k] = v

        if endpoint in ['_mapping']:
            r = requests.get(cls.target() + recid + endpoint)
        else:
            r = requests.post(cls.target() + recid + endpoint, data=json.dumps(query))
        return r.json


class Record(DomainObject):
    __type__ = 'record'

    @classmethod
    def make_rid(cls,data):
        id_data = {
            'author': [i.get('name','') for i in data.get('author',[])].sort(),
            'title': data.get('title','')
        }
        buf = util.slugify(json.dumps(id_data, sort_keys=True).decode('unicode-escape'),delim=u'')
        new_id = hashlib.md5(buf).hexdigest()
        return new_id

    @classmethod
    def sameas(cls,rid):
        res = cls.query(terms={'_sameas':rid})
        if res['hits']['total'] == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    @classmethod
    def merge(cls, a, b) :
        for k, v in a.items():
            if k.startswith('_') and k not in ['_collection']:
                del a[k]
            elif isinstance(v, dict) and k in b:
                cls.merge(v, b[k])
            elif isinstance(v, list) and k in b:
                if not isinstance(b[k], list):
                    b[k] = [b[k]]
                for idx, item in enumerate(v):
                    if isinstance(item,dict) and idx < len(b[k]):
                        cls.merge(v[idx],b[k][idx])
                    elif k in ['_collection'] and item not in b[k]:
                        b[k].append(item)
        a.update(b)
        return a

    # remove a record from a collection - bypasses the main save which always tries to greedily retain info    
    def removefromcollection(self,collid):
        if collid in self.data.get('_collection',[]):
            self.data.get('_collection',[].remove(collid))
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        Archive.store(self.data)

    # returns the collections of this record, split into two - yours, and not yours
    @property
    def isin(self):
        colls = {'yours':[],'other':[]}
        for item in self.data['_collection']:
            if item.startswith(current_user.id):
                colls['yours'].append(item.replace(current_user.id,''))
            else:
                colls['other'].append(item)
        return colls
            
    def save(self):
        # make an ID based on current content - builds from authors and title
        currid = self.make_rid(self.data)
        
        # get record with the current ID, if it already exists, and if so merge it
        exists = Record.get(currid)
        if exists:
            self.data = self.merge(self.data, exists.data)

        # if this record has a mismatched ID, check if it already exists
        # if so dedupe by merge then delete the old one
        if self.id and self.id != currid:
            old = Record.get(self.id)
            if old:
                self.data = cls.merge(self.data, old.data)
                if '_sameas' not in self.data: self.data['_sameas'] = []
                self.data['_sameas'].append(self.id)
                old.delete()
                
        self.data['_id'] = currid
        
        if 'SITE_URL' in app.config:
            self.data['url'] = app.config['SITE_URL'].rstrip('/') + '/record/' +  self.id
            if 'identifier' not in self.data: self.data['identifier'] = []
            if 'bibsoup' not in [i['type'] for i in self.data['identifier']]:
                self.data['identifier'].append({'type':'bibsoup','url':self.data['url'],'id':self.id})
        if '_created' not in self.data:
            self.data['_created'] = datetime.now().strftime("%Y-%m-%d %H%M")
        self.data['_last_modified'] = datetime.now().strftime("%Y-%m-%d %H%M")
            
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))

        Archive.store(self.data)

    @classmethod
    def bulk(cls, records):
        for item in records:
            new = Record(**item)
            new.save()


    def delete(self):
        Archive.store(self.data, action='delete')
        r = requests.delete( self.target() + self.id )

    @property
    def valuelist(self):
        # a list of all the values in the record
        vals = []
        def valloop(obj):
            if isinstance(obj,dict):
                for item in obj:
                    valloop(obj[item])
            elif isinstance(obj,list):
                for thing in obj:
                    valloop(thing)
            else:
                vals.append(obj)
        valloop(self.data)
        return vals
        
    @property
    def valuelist_string(self):
        return json.dumps(self.valuelist)

    @property
    def similar(self):
        res = Record.query(recid=self.id, endpoint='_mlt', q='mlt_fields=title&min_term_freq=1&percent_terms_to_match=1&min_word_len=3')
        return [i['_source'] for i in res['hits']['hits']]
    
    @property
    def remote(self):
        # check any listed external APIs for relevant data to return
        # TODO: just does service core for now - implement for others
        info = {}
        apis = app.config['EXTERNAL_APIS']
        if apis['servicecore']['key']:
            try:
                servicecore = "not found in any UK repository"
                addr = apis['servicecore']['url'] + self.data['title'].replace(' ','%20') + "?format=json&api_key=" + apis['servicecore']['key']
                r = requests.get(addr)
                data = r.json
                if 'ListRecords' in data and len(data['ListRecords']) != 0:
                    info['servicecore'] = data['ListRecords'][0]['record']['metadata']['oai_dc:dc']
            except:
                pass
        return info

    # build how it should look on the page
    @property
    def pretty(self):
        result = '<p>'
        img = False
        if img:
            result += '<img class="thumbnail" style="float:left; width:100px; margin:0 5px 10px 0; max-height:150px;" src="' + img[0] + '" />'

        # add the record based on display template if available
        record = self.data
        display = app.config['SEARCH_RESULT_DISPLAY']
        lines = ''
        for lineitem in display:
            line = ''
            for obj in lineitem:
                thekey = obj['field']
                parts = thekey.split('.')
                if len(parts) == 1:
                    res = record
                elif len(parts) == 2:
                    res = record.get(parts[0],'')
                elif len(parts) == 3:
                    res = record.get(parts[0],{}).get(parts[1],'')
                counter = len(parts) - 1
                if res and isinstance(res, dict):
                    thevalue = res.get(parts[counter],'')  # this is a dict
                else:
                    thevalue = []
                    for row in res:
                        thevalue.append(row[parts[counter]])

                if thevalue and len(thevalue):
                    line += obj.get('pre','')
                    if isinstance(thevalue, list):
                        for index,val in enumerate(thevalue):
                            if index != 0 and index != len(thevalue)-1: line += ', '
                            line += val
                    else:
                        line += thevalue
                    line += obj.get('post','')
            if line:
                lines += line + "<br />"
        if lines:
            result += lines
        else:
            result += json.dumps(record,sort_keys=True,indent=4)
        result += '</p>'
        return result


class Collection(DomainObject):
    __type__ = 'collection'

    def records(self, **kwargs):
        return [Record.get(**i['_source']['_id']) for i in Record.query(terms={'_collection':self.id}, **kwargs).get('hits',{}).get('hits',[])]

    def save(self):
        if not self.id:
            url = app.config.get('SITE_URL','').rstrip('/') + '/'
            if self.owner:
                url += self.owner + '/'
            slug = util.slugify(self.data.get('name',uuid.uuid4().hex))
            self.data['_id'] = self.owner + slug
            self.data['url'] = url + slug
        if '_created' not in self.data:
            self.data['_created'] = datetime.now().strftime("%Y-%m-%d %H%M")
        self.data['_last_modified'] = datetime.now().strftime("%Y-%m-%d %H%M")
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))

    def delete(self):
        r = requests.delete( self.target() + self.id )
        count = 0
        while count < len(self):
            for record in self.records(_from=count,size=100):
                record.data['_collection'].remove(self.id)
                record.save()
            count += 100
    
    def __len__(self):
        return Record.query(terms={'_collection':self.id}).get('hits',{}).get('total',0)

    @property
    def owner(self):
        '''Get id of this object.'''
        return self.data.get('owner', '')

    
class Archive(DomainObject, UserMixin):
    __type__ = 'archive'
    
    @classmethod
    def store(cls, data, action='update'):
        archive = Archive.get(data.get('_id',None))
        if not archive:
            return None
        if not archive.data['store']: archive.data['store'] = []
        archive.data['store'].append({'user': current_user.id, 'state': data, 'action':action})
        archive.save()
    
    
class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def get_by_email(cls,email):
        res = cls.query(terms={'email':email})
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return bibserver.auth.user.is_super(self)

    @property
    def email(self):
        return self.data['email']

    def collections(self, **kwargs):
        return [Collection.get(i['_source']['_id']) for i in Collection.query(terms={'owner':self.id},**kwargs).get('hits',{}).get('hits',[])]
    
    def __len__(self):
        return Collection.query(terms={'owner':self.id}).get('hits',{}).get('total',0)

    def delete(self):
        r = requests.delete( self.target() + self.id )
        count = 0
        while count < len(self):
            for coll in self.collections(_from=count,size=100):
                coll.delete()
            count += 100



# the data import manager
# gets an uploaded file or retrieves a file from a URL
# Uses the parser manager to parse the file
# indexes the records found in the file by upserting via the DAO
import urllib2
from datetime import datetime
import re
from cStringIO import StringIO
import unicodedata

from bibserver.parser import Parser
import bibserver.dao
import bibserver.util as util
from bibserver.config import config

class Importer(object):
    def __init__(self, owner, requesturl=False):
        self.owner = owner
        self.requesturl = requesturl

    def upload(self, fileobj, format_, collection=None):
        '''Import a collection into the database.
       
        :param fileobj: a fileobj pointing to file from which to import
        collection records (and possibly collection metadata)
        :param format_: format of the fileobj (e.g. bibtex)
        :param collection: collection dict for use when creating collection. If
        undefined collection must be extractable from the fileobj.

        :return: same as `index` method.
        '''
        parser = Parser()
        record_dicts = parser.parse(fileobj, format=format_)
        #collection_from_parser = None
        #if collection_from_parser:
        #    collection = collection_from_parser
        # TODO: check authz for write to this collection
        return self.index(collection, record_dicts)

    def upload_from_web(self, request):
        '''
        :param request_data: Flask request.values attribute.
        '''
        format = 'bibtex'
        source = ''
        fileobj = None
        if request.values.get("source"):
            source = urllib2.unquote(request.values.get("source", ''))
            fileobj = urllib2.urlopen(source)
            format = self.findformat(source)
        elif request.files.get('upfile'):
            fileobj = request.files.get('upfile')
            format = self.findformat(fileobj.filename)
        elif request.json:
            # see flask repo for further info
            # https://github.com/mitsuhiko/flask/issues/110
            # TODO: these are not working. see following comment
            fileobj = StringIO(request.json)
        elif request.data:
            fileobj = StringIO(request.data)

        if request.values.get('format'):
            format = request.values.get('format')

        # request.data and request.json never appear to have content
        # can solve by getting it out of the key it appears to get stuck into
        import json
        obj = ''
        for thing in request.values:
            if not request.values[thing] and not obj:
                obj = thing
        if obj and not fileobj:
            fileobj = StringIO(obj)
        # end of request data oddity

        if not 'collection' in request.values:
            raise ValueError('You must provide a collection label')
        collection = {
            'label': request.values['collection'],
            'source': source,
            'format': format
            }
        collection, records = self.upload(fileobj, format, collection)
        return (collection, records)

    def findformat(self,filename):
        if filename.endswith(".json"): return "json"
        if filename.endswith(".bibjson"): return "bibjson"
        if filename.endswith(".bibtex"): return "bibtex"
        if filename.endswith(".bib"): return "bibtex"
        if filename.endswith(".csv"): return "csv"
        return "bibtex"
    
    def bulk_upload(self, colls_list):
        '''upload a list of collections from provided file locations.

        :param colls_list: a list of dictionaries with 3 keys::

            {
                # source = url source for data
                # upfile = local file path for data
                # data = raw data
                source | upfile | data: ...,
                format: {the-format-of-the-data-e.g.-bibtex},
                collection: {label for the collection}
            }
        '''
        for coll in colls_list["collections"]:
            if "upfile" in coll:
                fileobj = coll["upfile"]
            elif "data" in coll:
                fileobj = StringIO(coll['data'])
            elif "source" in coll:
                fileobj = urllib2.urlopen(coll["source"])
            format_ = coll['format']
            collection_dict = {
                'label': coll['collection']
                }
            self.upload(fileobj, format_, collection_dict)
        return True
    
    def index(self, collection_dict, record_dicts):
        '''Add this collection and its records to the database index.
        :return: (collection, records) tuple of collection and associated
        record objects.
        '''
        collection = bibserver.dao.Collection(**collection_dict)
        timestamp = datetime.now().isoformat()
        collection['created'] = timestamp
        assert 'label' in collection, 'Collection must have a label'
        if not 'id' in collection:
            collection['id'] = util.slugify(collection['label'])
        collection['owner'] = self.owner.id

        delid = collection['id']
        for coll in self.owner.collections:
            if 'source' in coll and 'source' in collection:
                if coll['source'] == collection['source']:
                    if coll['id'] != collection['id']:
                        delid = coll['id']
                        bibserver.dao.Collection.delete_by_query('id:' + coll['id'])
                        break
                    else:
                        collection = coll
                        break
            if coll['id'] == collection['id']:
                collection = coll
                break

        bibserver.dao.Record.delete_by_query('collection.exact:"' + delid + '"')

        collection['records'] = len(record_dicts)
        collection['modified'] = timestamp
        collection.save()

        for rec in record_dicts:
            if 'collection' in rec:
                if collection["id"] not in rec["collection"]:
                    rec['collection'].append(collection["id"])
            else:
                rec['collection'] = [collection["id"]]
            if not self.requesturl and 'SITE_URL' in config:
                self.requesturl = str(config['SITE_URL'])
            if self.requesturl:
                if not self.requesturl.endswith('/'):
                    self.requesturl += '/'
                rec['url'] = self.requesturl + 'record/'
                if 'citekey' in rec:
                    rec['url'] += collection['id'] + '/' + rec.get('citekey')
                else:
                    rec['url'] += rec['id']
        records = bibserver.dao.Record.bulk_upsert(record_dicts)
        return collection, records



    # parse potential people out of a record
    # check if they have a person record in bibsoup
    # if not create one
    # append person IDs to a person attribute of every record
    def parse_people(self,record):
        if "person" not in record:
            record["person"] = []
        if "author" in record:
            record["person"].extend(self.do_people(record["author"]))
        if "advisor" in record:
            record["person"].extend(self.do_people(record["advisor"]))
        if "editor" in record:
            record["person"].extend(self.do_people(record["editor"]))
        return record
    
    def do_people(self,people):
        persons = []
        if isinstance(people,str):
            persons = self.do_person(people)
        if isinstance(people,list):
            for person in people:
                persons.append(self.do_person(person))
        return persons
    
    def do_person(self,person_string):
        try:
            results = bibserver.dao.Record.query(q='type.exact:"person" AND alias.exact:"' + person_string + '"')
            if results["hits"]["total"] != 0:
                return results["hits"]["hits"][0]["_source"]["person"]

            looseresults = bibserver.dao.Record.query(q='type.exact:"person" AND "*' + person_string + '*"',flt=True,fields=["person"])
            if looseresults["hits"]["total"] != 0:
                tid = looseresults["hits"]["hits"][0]["_id"]
                data = bibserver.dao.Record.get(tid)
                if "alias" in data:
                    if person_string not in data["alias"]:
                        data["alias"].append(person_string)
                bibserver.dao.Record.upsert(data)

                return data["person"]

            ident = person_string.replace(" ","").replace(",","").replace(".","")
            data = {"person":ident,"type":"person","alias":[person_string]}
            bibserver.dao.Record.upsert(data)
            return ident

        except:
            return []


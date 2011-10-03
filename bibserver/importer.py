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


class Importer(object):
    def __init__(self, owner):
        self.owner = owner

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
        if request.values.get("source"):
            source = urllib2.unquote(request.values.get("source", ''))
            fileobj = urllib2.urlopen(source)
            format = self.findformat(source)
        elif request.files.get('upfile'):
            fileobj = request.files.get('upfile')
            format = self.findformat(fileobj.filename)
        elif request.values.get('data'):
            fileobj = StringIO(request.values['data'])
        if request.values.get('format'):
            format = request.values.get('format')

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
        if not 'slug' in collection:
            collection['slug'] = util.slugify(collection['label'])
        collection['owner'] = self.owner.id
        # check if there is an existing collection for this user with same
        # 'user provided id' (ie. slug) and if so use that instead
        for coll in self.owner.collections:
            if coll['slug'] == collection['slug']:
                collection = coll
                break
        collection['total_records'] = len(record_dicts)
        collection['modified'] = timestamp
        collection.save()
        # delete any old versions of the records
        # TODO: should we merge (ie. do upsert rather than delete all existing
        # ones)
        bibserver.dao.Record.delete_by_query('collection.exact:"' +
                collection['slug'] + '"')
        for rec in record_dicts:
            rec['collection'] = collection["slug"]
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


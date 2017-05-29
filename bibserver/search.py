
from flask import Flask, request, redirect, abort, make_response
from flask import render_template, flash
import bibserver.dao
from bibserver import auth
import json, httplib
from bibserver.config import config
import bibserver.util as util


class Search(object):

    def __init__(self,path,current_user):
        self.path = path.replace(".json","")
        self.current_user = current_user

        self.search_options = {
            'search_url': '/query?',
            'search_index': 'elasticsearch',
            'paging': { 'from': 0, 'size': 10 },
            'predefined_filters': {},
            'facets': config['search_facet_fields'],
            'result_display': config['search_result_display'],
            'addremovefacets': config['add_remove_facets']      # (full list could also be pulled from DAO)
        }

        self.parts = self.path.strip('/').split('/')


    def find(self):
        if bibserver.dao.Account.get(self.parts[0]):
            if len(self.parts) == 1:
                return self.account() # user account
            elif len(self.parts) == 2:
                if self.parts[1] == "collections":
                    return self.collections()
                else:
                    return self.collection() # get a collection
            elif len(self.parts) == 3:
                return self.record() # get a record in collection
        elif self.parts[0] == 'collections':
            return self.collections() # get search list of all collections
        elif len(self.parts) == 1:
            if self.parts[0] != 'search':
                self.search_options['q'] = self.parts[0]
            return self.default() # get search result of implicit search term
        elif len(self.parts) == 2:
            return self.implicit_facet() # get search result of implicit facet filter
        else:
            abort(404)

    def default(self):
        # default search page
        if util.request_wants_json():
            res = bibserver.dao.Record.query()
            resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            return render_template('search/index.html', 
                current_user=self.current_user, 
                search_options=json.dumps(self.search_options), 
                collection=None
            )
        

    def implicit_facet(self):
        self.search_options['predefined_filters'][self.parts[0]+config['facet_field']] = self.parts[1]
        # remove the implicit facet from facets
        for count,facet in enumerate(self.search_options['facets']):
            if facet['field'] == self.parts[0]+config['facet_field']:
                del self.search_options['facets'][count]
        if util.request_wants_json():
            res = bibserver.dao.Record.query(terms=self.search_options['predefined_filters'])
            resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            return render_template('search/index.html', 
                current_user=self.current_user, 
                search_options=json.dumps(self.search_options), 
                collection=None, 
                implicit=self.parts[0]+': ' + self.parts[1]
            )


    def collections(self):
        if len(self.parts) == 1:
            if util.request_wants_json():
                res = bibserver.dao.Collection.query(size=1000000)
                colls = [i['_source'] for i in res['hits']['hits']]
                resp = make_response( json.dumps(colls, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                # search collection records
                self.search_options['search_url'] = '/query/collection?'
                self.search_options['facets'] = [{'field':'owner','size':100},{'field':'_created','size':100}]
                self.search_options['result_display'] = [[{'pre':'<h3>','field':'label','post':'</h3>'}],[{'field':'description'}],[{'pre':'created by ','field':'owner'}]]
                self.search_options['result_display'] = config['colls_result_display']
                return render_template('collection/index.html', current_user=self.current_user, search_options=json.dumps(self.search_options), collection=None)
        elif len(self.parts) == 2:
            if self.parts[0] == "collections":
                acc = bibserver.dao.Account.get(self.parts[1])
            else:
                acc = bibserver.dao.Account.get(self.parts[0])
            if acc:
                resp = make_response( json.dumps([coll.data for coll in acc.collections], sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                abort(404)
        elif len(self.parts) == 3:
            coll = bibserver.dao.Collection.get_by_owner_coll(self.parts[1],self.parts[2])
            if coll:
                coll.data['records'] = len(coll)
                resp = make_response( json.dumps(coll.data, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                abort(404)
        else:
            abort(404)
            

    def record(self):
        found = None
        res = bibserver.dao.Record.query(terms = {
            'owner'+config['facet_field']:self.parts[0],
            'collection'+config['facet_field']:self.parts[1],
            'id'+config['facet_field']:self.parts[2]
        })
        if res['hits']['total'] == 0:
            rec = bibserver.dao.Record.get(self.parts[2])
            if rec: found = 1
        elif res['hits']['total'] == 1:
            rec = bibserver.dao.Record.get(res['hits']['hits'][0]['_id'])
            found = 1
        else:
            found = 2

        if not found:
            abort(404)
        elif found == 1:
            collection = bibserver.dao.Collection.get_by_owner_coll(rec.data['owner'],rec.data['collection'])
            if request.method == 'DELETE':
                if rec:
                    if not auth.collection.update(self.current_user, collection):
                        abort(401)
                    rec.delete()
                    abort(404)
                else:
                    abort(404)
            elif request.method == 'POST':
                if rec:
                    if not auth.collection.update(self.current_user, collection):
                        abort(401)
                    rec.data = request.json
                    rec.save()
                    resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
                    resp.mimetype = "application/json"
                    return resp
            else:
                if util.request_wants_json():
                    resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
                    resp.mimetype = "application/json"
                    return resp
                else:
                    admin = True if auth.collection.update(self.current_user, collection) else False
                    
                    # make a list of all the values in the record, for autocomplete on the search field
                    searchvals = []
                    def valloop(obj):
                        if isinstance(obj,dict):
                            for item in obj:
                                valloop(obj[item])
                        elif isinstance(obj,list):
                            for thing in obj:
                                valloop(thing)
                        else:
                            searchvals.append(obj)
                    valloop(rec.data)
                    
                    # get fuzzy like this
                    host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
                    db_path = config['ELASTIC_SEARCH_DB']
                    fullpath = '/' + db_path + '/record/' + rec.id + '/_mlt?mlt_fields=title&min_term_freq=1&percent_terms_to_match=1&min_word_len=3'                    
                    c = httplib.HTTPConnection(host)
                    c.request('GET', fullpath)
                    resp = c.getresponse()
                    res = json.loads(resp.read())
                    mlt = [i['_source'] for i in res['hits']['hits']]
                    
                    # get any notes
                    notes = bibserver.dao.Note.about(rec.id)
                    
                    # check service core for more data about the record
                    # TODO: should maybe move this into the record dao or something
                    # TODO: also, add in any other calls to external APIs
                    servicecore = ""
                    apis = config['external_apis']
                    if apis['servicecore']['key']:
                        try:
                            servicecore = "not found in any UK repository"
                            addr = apis['servicecore']['url'] + rec.data['title'].replace(' ','%20') + "?format=json&api_key=" + apis['servicecore']['key']
                            import urllib2
                            response = urllib2.urlopen( addr )
                            data = json.loads(response.read())

                            if 'ListRecords' in data and len(data['ListRecords']) != 0:
                                record = data['ListRecords'][0]['record']['metadata']['oai_dc:dc']
                                servicecore = "<h3>Availability</h3><p>This article is openly available in an institutional repository:</p>"
                                servicecore += '<p><a target="_blank" href="' + record["dc:source"] + '">' + record["dc:title"] + '</a><br />'
                                if "dc:description" in record:
                                    servicecore += record["dc:description"] + '<br /><br />'
                                servicecore += '</p>'
                        except:
                            pass
                    
                    # render the record with all extras
                    return render_template('record.html', 
                        record=json.dumps(rec.data), 
                        prettyrecord=self.prettify(rec.data),
                        objectrecord = rec.data,
                        searchvals=json.dumps(searchvals),
                        admin=admin,
                        notes=notes,
                        servicecore=servicecore,
                        mlt=mlt,
                        searchables=json.dumps(config["searchables"], sort_keys=True)
                    )
        else:
            if util.request_wants_json():
                resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                return render_template('record.html', multiple=[i['_source'] for i in res['hits']['hits']])


    def account(self):
        self.search_options['predefined_filters']['owner'+config['facet_field']] = self.parts[0]
        acc = bibserver.dao.Account.get(self.parts[0])

        if request.method == 'DELETE':
            if not auth.user.update(self.current_user,acc):
                abort(401)
            if acc: acc.delete()
            return ''
        elif request.method == 'POST':
            if not auth.user.update(self.current_user,acc):
                abort(401)
            info = request.json
            if info.get('_id',False):
                if info['_id'] != self.parts[0]:
                    acc = bibserver.dao.Account.get(info['_id'])
                else:
                    info['api_key'] = acc.data['api_key']
                    info['_created'] = acc.data['_created']
                    info['collection'] = acc.data['collection']
                    info['owner'] = acc.data['collection']
            acc.data = info
            if 'password' in info and not info['password'].startswith('sha1'):
                acc.set_password(info['password'])
            acc.save()
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            if util.request_wants_json():
                if not auth.user.update(self.current_user,acc):
                    abort(401)
                resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                admin = True if auth.user.update(self.current_user,acc) else False
                recordcount = bibserver.dao.Record.query(terms={'owner':acc.id})['hits']['total']
                collcount = bibserver.dao.Collection.query(terms={'owner':acc.id})['hits']['total']
                return render_template('account/view.html', 
                    current_user=self.current_user, 
                    search_options=json.dumps(self.search_options), 
                    record=json.dumps(acc.data), 
                    recordcount=recordcount,
                    collcount=collcount,
                    admin=admin,
                    account=acc,
                    superuser=auth.user.is_super(self.current_user)
                )


    def collection(self):
        # show the collection that matches parts[1]
        self.search_options['predefined_filters']['owner'] = self.parts[0]
        self.search_options['predefined_filters']['collection'] = self.parts[1]

        # remove the collection facet
        for count,facet in enumerate(self.search_options['facets']):
            if facet['field'] == 'collection'+config['facet_field']:
                del self.search_options['facets'][count]

        # look for collection metadata
        metadata = bibserver.dao.Collection.get_by_owner_coll(self.parts[0],self.parts[1])

        if request.method == 'DELETE':
            if metadata != None:
                if not auth.collection.update(self.current_user, metadata):
                    abort(401)
                else: metadata.delete()
                return ''
            else:
                if not auth.collection.create(self.current_user, None):
                    abort(401)
                else:
                    size = bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]})['hits']['total']
                    for rid in bibserver.dao.Record.query(terms={'owner':self.parts[0],'collection':self.parts[1]},size=size)['hits']['hits']:
                        record = bibserver.dao.Record.get(rid['_id'])
                        if record: record.delete()
                    return ''
        elif request.method == 'POST':
            if metadata != None:
                metadata.data = request.json
                metadata.save()
                return ''
            else: abort(404)
        else:
            if util.request_wants_json():
                out = {"metadata":metadata.data,"records":[]}
                out['metadata']['records'] = len(metadata)
                out['metadata']['query'] = request.url
                for rec in metadata.records:
                    out['records'].append(rec.data)
                resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                admin = True if metadata != None and auth.collection.update(self.current_user, metadata) else False
                if metadata and '_display_settings' in metadata:
                    self.search_options.update(metadata['_display_settings'])
                users = bibserver.dao.Account.query(size=1000000) # pass the userlist for autocomplete admin addition (could be ajax'd)
                userlist = [i['_source']['_id'] for i in users['hits']['hits']]
                return render_template('search/index.html', 
                    current_user=self.current_user, 
                    search_options=json.dumps(self.search_options), 
                    collection=metadata.data, 
                    record = json.dumps(metadata.data),
                    userlist=json.dumps(userlist),
                    request=request,
                    admin=admin
                )


    def prettify(self,record):
        result = '<p>'
        # given a result record, build how it should look on the page
        img = False
        if img:
            result += '<img class="thumbnail" style="float:left; width:100px; margin:0 5px 10px 0; max-height:150px;" src="' + img[0] + '" />'

        # add the record based on display template if available
        display = config['search_result_display']
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
                    res = record[parts[0]][parts[1]]

                counter = len(parts) - 1

                if res and isinstance(res, dict):
                    thevalue = res.get(parts[counter],'')  # this is a dict
                elif res and isinstance(res, basestring):
                    thevalue = res
                else:
                    thevalue = []
                    # print (type (res))
                    for row in res:
                        thevalue.append(
                            row if isinstance(row, basestring) else row[parts[counter]]
                        )

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




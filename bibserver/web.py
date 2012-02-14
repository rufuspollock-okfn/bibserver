import os
import urllib2
from copy import deepcopy
import unicodedata
import httplib
import json
from datetime import datetime

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

from copy import deepcopy

import bibserver.dao
import bibserver.util as util
from bibserver.parser import Parser
from bibserver.config import config
import bibserver.iomanager
import bibserver.importer
import bibserver.ingest
from bibserver.core import app, login_manager
from bibserver.view.account import blueprint as account
from bibserver import auth

app.register_blueprint(account, url_prefix='/account')


# NB: the decorator appears to kill the function for normal usage
@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = bibserver.dao.Account.get(userid)
    return out

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = bibserver.dao.Account.get(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = bibserver.dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = bibserver.dao.Account.get(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.route('/')
def home():
    # get list of available collections
    colls = None
    try:
        # really bloody annoying error on update of bibsoup results in it refusing to order by _created
        # have tried setting the mapping manually and by the default, but not working. works fine on test machine
        # switching to unordered
        #result = bibserver.dao.Collection.query(q="*",sort={"_created":{"order":"desc"}})
        result = bibserver.dao.Collection.query(q="*")
        if result["hits"]["total"] != 0:
            colls = [bibserver.dao.Collection.get(i['_source']['id']) for i in result["hits"]["hits"]]
    except:
        pass
    return render_template('home/index.html', colls=colls, upload=config["allow_upload"] )

@app.route('/account/<user>')
def account(user):
    if hasattr(current_user,'id'):
        if user == current_user.id:
            return render_template('account/view.html',current_user=current_user)

    flash('You are not that user. Or you are not logged in.')
    return redirect('/account/login')


@app.route('/faq')
def content():
    return render_template('home/faq.html', upload=config["allow_upload"])

@app.route('/collections')
@app.route('/collections/')
@app.route('/collections/<path:path>', methods=['GET','POST'])
def collections(path=''):
    JSON = False
    if path.endswith(".json") or request.values.get('format',"") == "json":
        path = path.replace(".json","")
        JSON = True

    user = False
    coll = False
    if path:
        user, coll = path.split('/')

    # do request for specific collection record
    if coll:
        try:
            resid = bibserver.dao.Collection.query(terms={"owner":user,"collection":coll})['hits']['hits'][0]['_source']['id']
            res = bibserver.dao.Collection.get(resid)
        except:
            abort(404)
            
        # if POST, do update / create / delete
        if request.method == "POST" or (request.method == 'GET' and 'delete' in request.values):
            if not auth.collection.create(current_user, None):
                abort(401)

            if 'delete' in request.values:
                if not current_user['id'] == res['owner']:
                    abort(401)
                bibserver.dao.Collection.delete_by_query(q='owner:"'+user+'" AND collection:"'+coll+'"')
                bibserver.dao.Record.delete_by_query('collection'+config["facet_field"]+':"' + coll + '" AND owner'+config["facet_field"]+':"' + user + '"')
                if request.method == 'GET':
                    flash('Collection ' + coll + 'belonging to ' +  + ' deleted')
                    return redirect('/account/' + current_user['id'])
                else:
                    resp = make_response( '{"id":"' + res.id + '","deleted":true}' )
                    resp.mimetype = "application/json"
                    return resp
            
            # if not deleting, do the update    
            newrecord = request.json
            recobj = bibserver.dao.Collection(**newrecord)
            recobj.save()
            # TODO: should pass a better success / failure output
            resp = make_response( '{"id":"' + recobj.id + '","action":"updated"}' )
            resp.mimetype = "application/json"
            return resp

        # otherwise just serve collection metadata record
        if JSON:
            return outputJSON(coll=res)
        else:
            edit = False
            if auth.collection.update(current_user, res):
                edit = True
            if request.values.get('display_settings',''):
                # display the page for editing collection layout
                results = bibserver.dao.Record.query(q='collection'+config['facet_field']+':"'+res['collection']+'" AND owner'+config['facet_field']+':"'+current_user.id+'"',size=1000)
                io = bibserver.iomanager.IOManager(results=results, incollection=res)
                return render_template('collections/display_settings.html', upload=config["allow_upload"], coll=res, edit=edit, io=io)
            else:
                return render_template('collections/view.html', upload=config["allow_upload"], version=res.version, edit=edit)

    # do overall collections list page
    io = dosearch(path,'Collection')
    if JSON:
        return outputJSON(results=io.results, coll=io.incollection)
    else:
        return render_template('collections/index.html', upload=config["allow_upload"], io=io)

@app.route('/query', methods=['GET','POST'])
def query():
    qs = request.query_string
    if request.method == "GET":
        resp = make_response( bibserver.dao.Record.raw_query(qs) )
    if request.method == "POST":
        qs += "&source=" + json.dumps(dict(request.form).keys()[-1])
        resp = make_response( bibserver.dao.Record.raw_query(qs) )
    resp.mimetype = "application/json"
    return resp

class UploadView(MethodView):
    '''The upload view.

    upload from URL provided in source, or from file upload button, or from
    POST default format is bibtex, but accept other format specifications via
    format default upload is a collection, but could also be person or group
    record
    '''
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        if request.values.get("source") is not None:
            return self.post()
            
        return render_template('upload.html', upload=config["allow_upload"], 
                               ingest_tickets = bibserver.ingest.get_tickets())

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        try:
            collection = request.values.get('collection')
            ticket = bibserver.dao.IngestTicket.submit(owner=current_user.id, 
                                                       source_url=request.values.get("source"),
                                                       format=request.values.get('format'),
                                                       collection=request.values.get('collection'),
                                                       description=request.values.get('description'),
                                                       )
        except Exception, inst:
            msg = str(inst)
            if app.debug or app.config['TESTING']:
                raise
            return render_template('upload.html', upload=config["allow_upload"], msg=msg)
        else:
            return redirect('/ticket/'+ticket.id)

# enable upload unless not allowed in config
if config["allow_upload"] == "YES":
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))


# parse a file and return it as BibJSON
# expects ?source="http://some.web/addr.ext"&format=bibtex
# and optional collection="nice coll name"
@app.route('/parse')
def parse():
    # TODO: acceptable formats should be derived by some sort of introspection 
    # from the parser.py based on what parsers are actually available.
    if 'format' not in request.values or 'source' not in request.values:
        if 'format' not in request.values and 'source' not in request.values:
            resp = make_response( '{"error": "Parser cannot run without source URL parameter and source format parameter", "acceptable_formats": ["bibtex","json","csv"]}' )
        elif 'format' not in request.values:
            resp = make_response( '{"error": "Parser cannot run without source format parameter", "acceptable_formats": ["bibtex","json","csv"]}' )
        elif 'source' not in request.values:
            resp = make_response( '{"error": "Parser cannot run without source URL parameter"}')
        resp.mimetype = "application/json"
        return resp

    format = request.values.get("format").strip('"')
    source = request.values.get("source").strip('"')

    try:
        if not source.startswith('http://') and not source.startswith('https://'):
            source = 'http://' + source
        source = urllib2.unquote(source)
        fileobj = urllib2.urlopen(source)
    except:
        resp = make_response( '{"error": "Retrieval of file from source ' + source + ' failed"}' )
        resp.mimetype = "application/json"
        return resp

    parser = Parser()
    newcoll = {}
    newcoll['records'], newcoll['metadata'] = parser.parse(fileobj, format=format)
    newcoll['metadata']['source'] = source
    timestamp = datetime.now().isoformat()
    newcoll['metadata']['created'] = timestamp
    if request.values.get('collection',None):
        collection = request.values['collection'].strip('"')
        newcoll['metadata']['label'] = collection
        newcoll['metadata']['id'] = util.slugify(collection)
        for record in newcoll['records']:
            record['collection'] = newcoll['metadata']['id']
    resp = make_response( json.dumps(newcoll, sort_keys=True, indent=4) )
    resp.mimetype = "application/json"
    return resp

@app.route('/search')
@app.route('/<path:path>')
def search(path=''):
    bits = path.strip('/').split('/')
    if len(bits) == 3:
        return record(user=bits[0],coll=bits[1],sid=bits[2])
    else:
        io = dosearch(path.replace(".json",""),'Record')
        if path.endswith(".json") or request.values.get('format',"") == "json":
            return outputJSON(results=io.set(), coll=io.incollection, facets=io.results.get('facets',None))
        else:
            edit = False
            if io.incollection:
                if auth.collection.update(current_user, io.incollection):
                    edit = True
            return render_template('search/index.html', upload=config["allow_upload"], io=io, edit=edit)

def dosearch(path,searchtype='Record'):
    # set query info
    args = {"terms":{}}
    if 'from' in request.values:
        args['start'] = request.values.get('from')
    if 'size' in request.values:
        args['size'] = request.values.get('size')
    if 'sort' in request.values:
        if request.values.get("sort") != "..." and request.values.get("sort") != "":
            args['sort'] = {request.values.get('sort') : {"order" : request.values.get('order','asc')}}
    if 'default_operator' in request.values:
        args['default_operator'] = request.values['default_operator']
    if 'q' in request.values:
        if len(request.values.get('q')) > 0:
            args['q'] = request.values.get('q')
            args['q'] = args['q'].replace('!','')
            if '"' in args['q'] and args['q'].count('"')%2 != 0:
                args['q'] = args['q'].replace('"','')
            if ' OR ' in request.values['q']:
                args['default_operator'] = 'OR'
            if ' AND ' in request.values['q']:
                args['default_operator'] = 'AND'
            argparts = args['q'].split(' ')
            for index,part in enumerate(argparts):
                if part.startswith(':') or part.endswith(':'):
                    argparts[index] = "'" + part + "'"
            args['q'] = ' '.join(argparts)
            #args['q'] = "'" + args['q'] + "'"
                
    
    # set implicit keys / collections
    incollection = {}
    implicit_key = False
    implicit_value = False
    if path != '' and not path.startswith("search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/')
        if len(bits) == 2:
            # if first bit is a user ID then this is a collection
            if bibserver.dao.Account.get(bits[0]):
                try:
                    find = bibserver.dao.Collection.query(terms={"owner":bits[0],"collection":bits[1]})['hits']['hits'][0]['_source']['id']
                    incollection = bibserver.dao.Collection.get(find)
                except:
                    pass
                bits[0] = 'collection'
            implicit_key = bits[0]
            implicit_value = bits[1]

    # set facet fields from params or from collections settings or from general config
    args['facet_fields'] = []
    try:
        facets = deepcopy(incollection['display_settings']['facet_fields'])
    except:
        facets = deepcopy(config["facet_fields"])
    if request.values.get('showfacets',None):
        for item in request.values['showfacets'].split(','):
            if item in facets:
                args['facet_fields'].append(facets[item])
            else:
                args['facet_fields'].append({ "key": item+config["facet_field"], "size": "100", "order": "count" })
    else:
        args['facet_fields'] = facets
    for item in args['facet_fields']:
        if not item['key'].endswith(config["facet_field"]):
            item['key'] = item['key']+config["facet_field"]

    for param in request.values:
        if param in [i['key'].replace(config['facet_field'],'') for i in args['facet_fields']]:
            vals = json.loads(unicodedata.normalize('NFKD',urllib2.unquote(request.values.get(param))).encode('utf-8','ignore'))
            args['terms'][param + config['facet_field']] = vals
    if implicit_key:
        args['terms'][implicit_key+config['facet_field']] = [implicit_value]
    if incollection:
        args['terms']['owner'+config['facet_field']] = incollection['owner']

    # save current display settings if requested
    if incollection:
        if 'savedisplay' in request.values:
            if auth.collection.update(current_user, incollection):
                if 'display_settings' not in incollection:
                    incollection['display_settings'] = {}
                incollection['display_settings']['facet_fields'] = args['facet_fields']
                for item in incollection['display_settings']['facet_fields']:
                    if item['key'].endswith(config["facet_field"]):
                        item['key'] = item['key'].replace(config["facet_field"],'')
                incollection.save()
                flash('Display settings saved.')

    if searchtype == 'Record':
        results = bibserver.dao.Record.query(**args)
    else:
        results = bibserver.dao.Collection.query(**args)
    return bibserver.iomanager.IOManager(results, args, request.values.get('showkeys',None), incollection, implicit_key, implicit_value, path, request.values.get('showopts',''), facets, current_user)

def record(user,coll,sid):
    # POSTs do updates, creates, deletes of records
    if request.method == "POST":
        if not auth.collection.create(current_user, None):
            abort(401)
        if 'delete' in request.values:
            host = str(config['ELASTIC_SEARCH_HOST']).rstrip('/')
            db_name = config['ELASTIC_SEARCH_DB']
            fullpath = '/' + db_name + '/record/' + sid
            c =  httplib.HTTPConnection(host)
            c.request('DELETE', fullpath)
            c.getresponse()
            resp = make_response( '{"id":"' + sid + '","deleted":"yes"}' )
            resp.mimetype = "application/json"
            return resp
        
        # if not deleting, do the update    
        newrecord = request.json
        action = "updated"
        #if path == "create":
        #    if 'id' in newrecord:
        #        del newrecord['id']
        #    action = "new"
        recobj = bibserver.dao.Record(**newrecord)
        recobj.save()
        # TODO: should pass a better success / failure output
        resp = make_response( '{"id":"' + recobj.id + '","action":"' + action + '"}' )
        resp.mimetype = "application/json"
        return resp
    else:
        # otherwise do the GET of the record
        JSON = False
        if sid.endswith(".json") or request.values.get('format',"") == "json":
            sid = sid.replace(".json","")
            JSON = True
        
        #if path == "create":
        #    if not auth.collection.create(current_user, None):
        #        abort(401)
        #    return render_template('create.html')

        if app.config['TESTING']:
            # TODO: running the test may not create mappings properly, hence searches on the unanalysed versions of a field fail
            res = bibserver.dao.Record.query(terms = {'owner':user.lower(),'collection':coll.lower(),'cid':sid.lower()})
            if res['hits']['total'] == 0:
                res = bibserver.dao.Record.query(terms = {'id':sid.lower()})
        else:
            res = bibserver.dao.Record.query(terms = {'owner'+config['facet_field']:user,'collection'+config['facet_field']:coll,'cid'+config['facet_field']:sid})
            if res['hits']['total'] == 0:
                res = bibserver.dao.Record.query(terms = {'id'+config['facet_field']:sid})

        if JSON:
            return outputJSON(results=[i['_source'] for i in res['hits']['hits']], record=True)
        else:
            if res["hits"]["total"] == 0:
                abort(404)
            elif res["hits"]["total"] != 1:
                io = bibserver.iomanager.IOManager(res)
                return render_template('record.html', io=io, multiple=True)
            else:
                io = bibserver.iomanager.IOManager(res)
                getcoll = bibserver.dao.Collection.query(terms={'owner':user,'collection':coll})
                if getcoll['hits']['total'] == 1:
                    thecoll = getcoll['hits']['hits'][0]['_source']
                else:
                    thecoll = False
                if thecoll and auth.collection.update(current_user, thecoll) and config["allow_edit"] == "YES":
                    edit = True
                else:
                    edit = False
                return render_template('record.html', io=io, edit=edit, upload=config["allow_upload"])

def outputJSON(results=None, coll=None, facets=None, record=False):
    '''build a JSON response, with metadata unless specifically asked to suppress'''
    # TODO: in some circumstances, people data should be added to collections too.
    out = {"metadata":{}}
    if coll:
        out['metadata'] = coll.data
        out['metadata']['records'] = len(coll)
    out['metadata']['query'] = request.base_url + '?' + request.query_string
    if request.values.get('facets','') and facets:
        out['facets'] = facets
    out['metadata']['from'] = request.values.get('from',0)
    out['metadata']['size'] = request.values.get('size',10)

    if results:
        out['records'] = results

        # if a single record meta default is false
        if record and len(out['records']) == 1 and not request.values.get('meta',False):
            out = out['records'][0]

        # if a search result meta default is true
        meta = request.values.get('meta',True)
        if meta == "False" or meta == "false" or meta == "no" or meta == "No" or meta == 0:
            meta = False
        #if not record and not meta:
        if not record and not meta:
            out = out['records']
            if len(out) == 1:
                out = out[0]
    elif coll:
        out = coll.data
    else:
        out = {}

    resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
    resp.mimetype = "application/json"
    return resp

if __name__ == "__main__":
    bibserver.dao.init_db()
    app.run(host='0.0.0.0', debug=True)


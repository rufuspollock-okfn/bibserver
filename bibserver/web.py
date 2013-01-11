import os
import urllib2
import unicodedata
import json
from copy import deepcopy
from datetime import datetime

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flask.ext.login import login_user, current_user

import bibserver.dao
import bibserver.util as util
import bibserver.importer
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
    return dict(current_user=current_user, app=app)

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
            user = bibserver.dao.Account.get(res[0]['_source']['_id'])
            if user:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401


@app.route('/query/<path:path>', methods=['GET','POST'])
@app.route('/query/', methods=['GET','POST'])
@app.route('/query', methods=['GET','POST'])
@util.jsonp
def query(path='Record'):
    pathparts = path.split('/')
    subpath = pathparts[0]
    if subpath.lower() == 'account':
        abort(401)
    klass = getattr(bibserver.dao, subpath[0].capitalize() + subpath[1:] )
    if len(pathparts) > 1 and pathparts[1] == '_mapping':
        resp = make_response( json.dumps(klass().query(endpoint='_mapping')) )
    elif len(pathparts) == 2 and pathparts[1] not in ['_mapping','_search']:
        if request.method == 'POST':
            abort(401)
        else:
            rec = klass().get(pathparts[1])
            if rec:
                resp = make_response( rec.json )
            else:
                abort(404)
    else:
        if request.method == "POST":
            if request.json:
                qs = request.json
            else:
                try:
                    qs = dict(request.form).keys()[-1]
                except:
                    abort(411)
        elif 'q' in request.values:
            qs = {'query': {'query_string': { 'query': request.values['q'] }}}
        elif 'source' in request.values:
            qs = json.loads(urllib2.unquote(request.values['source']))
        else: 
            qs = request.query_string
        for item in request.values:
            if item not in ['q','source','callback','_'] and isinstance(qs,dict):
                qs[item] = request.values[item]
        res = klass().query(q=qs)
        resp = make_response( json.dumps( res ) )

        # track queries submitted, if usage tracking is on
        if app.config.get('QUERY_TRACKING', False):
            if current_user.is_anonymous():
                who = 'anonymous'
            else:
                who = current_user.id
            dets = {
                'query': qs,
                'querystring': json.dumps(qs),
                'method': request.method,
                'source': request.remote_addr,
                'xhr': request.is_xhr,
                'resultsize': res.get('hits',{}).get('total',0),
                'user': who
            }
            track = bibserver.dao.SearchHistory(**dets)
            track.save()

    resp.mimetype = "application/json"
    return resp
        

@app.route('/')
def home():
    data = []
    colldata = bibserver.dao.Collection.query(sort={"_created.exact":{"order":"desc"}},size=1000).get('hits',{}).get('hits',[])
    for coll in colldata:
        colln = bibserver.dao.Collection.get(coll['_id'])
        if colln:
            data.append({
                'name': colln.data['name'], 
                'records': len(colln), 
                'owner': colln.owner, 
                'slug': colln.data['slug'],
                'description': colln.data.get('description','')
            })
    # if there are no registered collections, check for implicit ones
    # e.g. records that are recorded as being in a collection, but that collection has no record itself
    if not data:
        colldata = bibserver.dao.Record.query(size=0, facets={'colls':{'terms':{'field':'_collection'}}})
        if colldata:
            for colln in colldata.get('facets',{}).get('colls',{}).get('terms',[]):
                data.append({
                    'name': colln['term'], 
                    'records': colln['count'], 
                    'owner': '', 
                    'slug': colln['term'],
                    'description': ''
                })
    colls = bibserver.dao.Collection.query().get('hits',{}).get('total',0)
    records = bibserver.dao.Record.query().get('hits',{}).get('total',0)
    users = bibserver.dao.Account.query().get('hits',{}).get('total',0)
    flash('Hi there, welcome to the new BibSoup. Please read <a target="_blank" href="http://openbiblio.net/2013/01/11/a-revamp-of-bibserver-and-bibsoup/">our latest post to learn about recent changes.')
    return render_template('home/index.html', colldata=json.dumps(data), colls=colls, records=records, users=users)


# upload from a bibjson file
class UploadView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to upload a collection.')
            return redirect('/account/login')
        return render_template('upload.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(403)
        elif not request.values.get('source',False) and not request.files.get('upfile',False) and not request.json:
            flash('Sorry, you need to provide a source URL or a source file (or POST some JSON via the API).')        
        else:
            if request.values.get('source'):
                r = requests.get( request.values['source'].strip() )
                data = json.loads(r.content)
            elif request.files.get('upfile'):
                fileobj = request.files.get('upfile')
                data = json.load(fileobj)
            elif request.json:
                data = request.json
            else:
                abort(409)

            importer = bibserver.importer.Importer(data, request.values.get('collection',''), current_user.id, current_user.email)
            importer.start()

            flash('Thanks. Your records are being uploaded. You will receive an email when upload is complete. Please check back soon for updates.', 'success')
        return render_template('upload.html')
            
# create new collection / record
class CreateView(MethodView):
    def get(self, rtype=''):
        if not auth.collection.create(current_user, None):
            flash('You need to login to create a collection.')
            return redirect('/account/login')
        else:
            return render_template('create.html', rtype=rtype)

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        elif request.values.get('collection',False):
            # create a new collection
            # new records are POSTed directly to /record
            coll = bibserver.dao.Collection.get(current_user.id + '/' + util.slugify(request.values['collection']))
            if coll is not None:
                flash('Sorry! You already have a collection named ' + request.values['collection'])
                return render_template('create.html')
            else:
                collection = bibserver.dao.Collection(
                    name = request.values['collection'],
                    description = request.values.get('description',''),
                    license = request.values.get('license',''),
                    owner = current_user.id
                )
                collection.save()
                return redirect(collection.owner + '/' + collection.data['slug']
        else:
            abort(400)

# a class for use when upload / create are disabled
class NoUploadOrCreate(MethodView):
    def get(self):
        return render_template('disabled.html')
    def post(self):
        abort(403)

# set the upload / create views as appropriate
if app.config.get("ALLOW_UPLOAD",False):
    app.add_url_rule('/upload', view_func=UploadView.as_view('upload'))
    app.add_url_rule('/create', view_func=CreateView.as_view('create'))
    app.add_url_rule('/create/<rtype>', view_func=CreateView.as_view('create'))
else:
    app.add_url_rule('/upload', view_func=NoUploadOrCreate.as_view('upload'))
    app.add_url_rule('/create', view_func=NoUploadOrCreate.as_view('create'))
    app.add_url_rule('/create/<rtype>', view_func=NoUploadOrCreate.as_view('create'))


# expose the record ID maker to POST
@app.route('/record/make_rid', methods=['GET','POST'])
def make_rid():
    if request.method == 'POST':
        data = request.json
    else:
        data = request.values.get('source',False)
    if data:
        return bibserver.dao.Record.make_rid(data)
    else:
        abort(400)


# a place to see what tags a record has, or to add a tag to a record
@app.route('/record/<rid>/tags',methods=['GET'])
@app.route('/record/<rid>/tags/<tagid>', methods=['POST','DELETE'])
def tag(rid,tagid=''):
    rec = bibserver.dao.Record.get(rid.replace(".json",""))
    # check for sameas on non find
    if not rec:
        sameas = bibserver.dao.Record.sameas(rid)
        if sameas:
            return redirect('/record/' + sameas.id + '/collections')
        else:
            abort(404)

    if tagid == '':
        # show a list of the collections this record is in
        resp = make_response( json.dumps(rec.data.get('_tag',[]), indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif not current_user.is_anonymous():
        if request.method == 'POST':
            rec.addtag(tagid)
        elif request.method == 'DELETE':
            rec.removetag(tagid)
        return ''

        
# a place to see what collections a record is in, or to add a record to a collection
@app.route('/record/<rid>/collections',methods=['GET'])
@app.route('/record/<rid>/collections/<collid>', methods=['POST','DELETE'])
@app.route('/record/<rid>/collections/<collowner>/<collslug>', methods=['POST','DELETE'])
def recollection(rid,collid='',collowner='',collslug=''):
    rec = bibserver.dao.Record.get(rid.replace(".json",""))
    # check for sameas on non find
    if not rec:
        sameas = bibserver.dao.Record.sameas(rid)
        if sameas:
            return redirect('/record/' + sameas.id + '/collections')
        else:
            abort(404)

    if collowner != '':
        collid = collowner + '_____' + collslug

    if collid == '':
        # show a list of the collections this record is in
        resp = make_response( json.dumps(rec.data['_collection'], indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif not current_user.is_anonymous():
        coll = bibserver.dao.Collection.get(collid)
        if (coll and auth.collection.update(current_user,coll)) or not coll:
            if request.method == 'POST':
                rec.addtocollection(collid)
            elif request.method == 'DELETE':
                rec.removefromcollection(collid)
        return ''
    

# set the route for viewing records
@app.route('/record', methods=['GET','POST'])
@app.route('/record/<rid>', methods=['GET','POST','DELETE'])
@util.jsonp
def record(rid=''):
    rec = bibserver.dao.Record.get(rid.replace(".json",""))
    
    # check for sameas on non find
    if not rec:
        sameas = bibserver.dao.Record.sameas(rid)
        if sameas:
            return redirect('/record/' + sameas.id)

    if request.method == 'DELETE':
        if current_user.is_anonymous() or not current_user.is_super():
            abort(403)
        elif rec:
            rec.delete()
        abort(404)
    elif request.method == 'POST':
        if current_user.is_anonymous() or not app.config.get("ALLOW_UPLOAD",False):
            abort(403)
        try:
            new = False
            if not rec:
                rec = bibserver.dao.Record()
                new = True
            if len(request.json):
                rec.data = request.json
                if new: rec.data['_created_by'] = current_user.id
                rec.save()
                resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
                resp.mimetype = "application/json"
                return resp
            else:
                abort(400)
        except:
            abort(400)
    elif rec and util.request_wants_json():
        resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif rec:        
        # add this to the recent viewed list of the current user if there is one
        if not current_user.is_anonymous():
            current_user.addrecentview((rec.id,rec.data.get('title','untitled record')))
        # render the record with all extras
        return render_template('record.html', rec=rec, disqus_shortname=app.config['DISQUS_RECORDS'], uploadable=app.config['INDEX_ATTACHMENTS'], searchables=app.config['SEARCHABLES'])
    else:
        abort(404)


# show all the collections
@app.route('/collections')
@app.route('/collections.json')
@util.jsonp
def collections(owner=''):
    if util.request_wants_json():
        if owner:
            terms = {'owner':owner}
        else:
            terms = {}
        res = bibserver.dao.Collection.query(_from=request.values.get('from',0), terms=terms)
        colls = [i['_source'] for i in res['hits']['hits']]
        resp = make_response( json.dumps(colls, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        search_options = deepcopy(app.config['FACETVIEW'])
        search_options['search_url'] = '/query/collection?'
        search_options['result_display'] = app.config['COLLECTIONS_RESULT_DISPLAY']
        search_options["searchwrap_start"] = '<div id="facetview_results" class="clearfix">'
        search_options["searchwrap_end"] = "</div>"
        search_options["resultwrap_start"] = '<div class="span3 img thumbnail result_box" style="margin-bottom:10px;height:100px;overflow:hidden;"><div class="result_info">'
        search_options["resultwrap_end"] = "</div></div>"
        search_options["paging"]["size"] = 12
        if owner:
            search_options["predefined_filters"] = {"owner": {"term": {'owner': owner}}}
        return render_template('collection/index.html', current_user=current_user, search_options=json.dumps(search_options), owner=owner, collection=None)


# this is a catch-all that allows us to present everything as a search
# typical catches are /collection, /user, /user/collection, /user/collection/record, 
# /implicit_facet_key/implicit_facet_value
# and any thing else passed as a search
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
@util.jsonp
def default(path):
    search_options = deepcopy(app.config['FACETVIEW'])
    search_options['result_display'] = deepcopy(app.config['SEARCH_RESULT_DISPLAY'])

    parts = path.strip('/').replace(".json","").split('/')

    implicit = ''
    acc = bibserver.dao.Account.get(parts[0])
    
    # check for an account validation request
    if acc is None and app.config['ACCOUNT_EMAIL_VALIDATION'] and request.values.get('validate',False):
        acc = bibserver.dao.UnapprovedAccount.get(parts[0])
        if acc is not None:
            validaccount = acc.validate(request.values['validate'])
            if validaccount is not None:
                flash('Thanks for validating! Your account is active. You should now login for the first time via the <a href="/account/login">login page</a>', 'success')
                acc = validaccount

    if len(parts) == 1 and acc is not None:
        return account(search_options,parts,path,acc)
    elif len(parts) == 1 and parts[0] != 'search':
        coll = bibserver.dao.Collection.get(parts[0])
        if coll is not None:
            return collection(coll,search_options,parts)
        else:
            search_options['q'] = '*' + parts[0].lstrip('*').rstrip('*') + '*'
    elif len(parts) == 2 and acc is not None and parts[1] == 'collections':
        return collections(owner=parts[0])
    elif len(parts) == 2 and acc is not None:
        coll = bibserver.dao.Collection.get(parts[0] + '/' + parts[1])
        return collection(coll,search_options,parts)
    elif len(parts) == 2:
        search_options['predefined_filters'] = {"implicit": {"term": {parts[0]+app.config['FACET_FIELD']: parts[1]}}}
        for count,facet in enumerate(search_options['facets']):
            if facet['field'] == parts[0]+app.config['FACET_FIELD']:
                del search_options['facets'][count]
        implicit = parts[0]+': ' + parts[1]
    elif len(parts) == 3:
        return account(search_options,parts,path,acc)

    if util.request_wants_json():
        res = bibserver.dao.Record.query()
        resp = make_response( json.dumps([i['_source'] for i in res['hits']['hits']], sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        search_options['facets'] = deepcopy(app.config['ALL_SEARCH_FACET_FIELDS'])
        return render_template('search/index.html', current_user=current_user, search_options=json.dumps(search_options), implicit=implicit, collection=None)


# present info about a given collection
def collection(coll,search_options,parts):
    search_options['facets'] = deepcopy(app.config['INCOLL_SEARCH_FACET_FIELDS'])
    if request.method == 'DELETE' and coll is not None and auth.collection.update(current_user,coll):
        coll.delete()
        abort(404)
    elif request.method == 'POST' and coll is not None and auth.collection.update(current_user,coll):
        if '_collection' in request.json:
            if isinstance('list',request.json['_collection']):
                request.json['_collection'] = coll.data['_collection'] + request.json['_collection']
            else:
                request.json['_collection'] = coll.data['_collection'].append(request.json['_collection'])
        coll.data = request.json
        coll.save()
        resp = make_response( json.dumps(pcoll.data, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif util.request_wants_json() and coll is not None:
        resp = make_response( json.dumps(coll.data, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    elif coll is not None:
        search_options['predefined_filters'] = {"_collection": {"term": {'_collection': coll.id}}}
        for count,facet in enumerate(search_options['facets']):
            if facet['field'] == '_collection'+app.config['FACET_FIELD']:
                del search_options['facets'][count]
        if not len(coll):
            flash('This collection appears to be empty. Go and <a href="/search">search</a> for some records to add to it, or <a href="/create">create</a> or <a href="/upload">upload</a> some new ones.')
        return render_template('search/index.html', current_user=current_user, search_options=json.dumps(search_options), implicit=None, collection=coll)
    else:
        abort(404)


# present info about a given user
# called from within the above default search, when the path is an account path
# done this way to enable flexible search paths first
def account(search_options,parts,path,acc):
    if len(parts) == 1:
        if request.method == 'DELETE' and acc and auth.user.update(current_user,acc):
            acc.delete()
            abort(404)
        elif request.method == 'POST' and auth.user.update(current_user,acc):
            info = request.json
            if info.get('_id',False):
                if info['_id'] != parts[0]:
                    acc = bibserver.dao.Account.get(info['_id'])
                else:
                    info['api_key'] = acc.data['api_key']
                    info['_created'] = acc.data['_created']
            acc.data = info
            if 'password' in info and not info['password'].startswith('sha1'):
                acc.set_password(info['password'])
            acc.save()
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        elif util.request_wants_json() and auth.user.update(current_user,acc):
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            admin = True if auth.user.update(current_user,acc) else False
            if not admin:
                flash('You are not logged in as ' + acc.id + '. Use the <a href="/account/login">login page</a> if you need to change this.')
            return render_template('account/view.html', 
                current_user=current_user, 
                admin = admin,
                account=acc
            )
    elif len(parts) == 3:
        coll = bibserver.dao.Collection.get(parts[0] + '/' + parts[1])
        rec = bibserver.dao.Record.get(parts[2])
        if request.method == 'DELETE' and coll and auth.collection.update(current_user,coll):
            rec.removefromcollection(parts[0] + '/' + parts[1])
            resp = make_response( json.dumps(rec.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        elif request.method == 'POST' and auth.collection.update(current_user,coll):
            if parts[0] + parts[1] not in rec.data['_collection']:
                rec.data['_collection'].append(parts[0] + '/' + parts[1])
                rec.save()
            return ''
        else:
            return redirect('/record/' + path.split('/')[-1] + '?' + request.query_string)


if __name__ == "__main__":
    app.run(host=app.config['HOST'], debug=app.config['DEBUG'], port=app.config['PORT'])


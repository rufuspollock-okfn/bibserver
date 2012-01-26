import json, urllib2
from copy import deepcopy
import operator, unicodedata
import bibserver.dao
import bibserver.config
import re

class IOManager(object):
    def __init__(self, results, args={}, showkeys='', incollection=False, implicit_key="", implicit_value="", path="", showopts="", facets=[], current_user=None):
        self.results = results
        self.args = args
        self.showopts = showopts
        self.showkeys = showkeys
        self.incollection = incollection
        self.implicit_key = implicit_key
        self.implicit_value = implicit_value
        self.path = path
        self.facets = facets
        self.config = bibserver.config.Config()
        self.result_display = self.config.result_display
        self.current_user = current_user

        self.facet_fields = self.args.get('facet_fields',self.config.facet_fields)
        for item in self.facet_fields:
            if item['key'].endswith(self.config.facet_field):
                item['key'] = item['key'].replace(self.config.facet_field, '')

        self.facet_values = {}
        if 'facets' in self.results:
            for facet,data in self.results['facets'].items():
                self.facet_values[facet.replace(self.config.facet_field,'')] = data["terms"]

    def get_q(self):
        return self.args.get('q','')
    
    def get_safe_terms_object(self):
        terms = {}
        for term in self.args["terms"]:
            if term.replace(self.config.facet_field,'') not in self.path:
                theterm = '['
                for i in self.args['terms'][term]:
                    theterm += '"' + i + '",'
                theterm = theterm[:-1]
                theterm += ']'
                terms[term.replace(self.config.facet_field,'')] = theterm
        return terms    

    def get_path_params(self,myargs={}):
        if not myargs:
            myargs = self.args
        param = '/' + self.path + '?' if (self.path != '') else self.config.base_url + '?'
        if 'q' in myargs:
            param += 'q=' + myargs['q'] + '&'
        if 'terms' in myargs:
            for term in myargs['terms']:
                if term.replace(self.config.facet_field,'') not in self.path:
                    val = '[' + ",".join(urllib2.quote('"{0}"'.format(i.encode('utf-8'))) for i in myargs['terms'][term]) + ']'
                    param += term.replace(self.config.facet_field,'') + '=' + val + '&'
        if self.showkeys:
            param += 'showkeys=' + self.showkeys + '&'
        if self.get_showfacets():
            param += 'showfacets=' + self.get_showfacets(format='string') + '&'
        return param

    def get_add_url(self, field, value):
        myargs = deepcopy(self.args)
        field += self.config.facet_field
        if myargs['terms'].has_key(field):
            if value not in myargs['terms'][field]:
                myargs['terms'][field].append(value)
        else:
            myargs['terms'][field] = [value]
        return self.get_path_params(myargs)
        
    def get_delete_url(self, field, value=None):
        myargs = deepcopy(self.args)
        if value is not None:
            field += self.config.facet_field
            myargs['terms'][field].remove(value)
            if len(myargs['terms'][field]) == 0:
                del myargs['terms'][field]
        else:
            del myargs['terms'][field]
        return self.get_path_params(myargs)


    def in_args(self, facet, value):
        return self.args['terms'].has_key(facet + self.config.facet_field) and value in self.args['terms'][facet + self.config.facet_field]
            
    def get_result_display(self,counter,display=None):
        '''use the result_display object as a template for search results'''
        output = ""

        if not display:
            display = self.result_display            
        if not display:
            return output

        for item in display:
            line = ""
            for pobj in item:
                if 'key' in pobj:
                    keydisp = self.get_str(self.set()[counter],pobj['key'])
                    if keydisp:
                        try:
                            keydisp = unichr(keydisp)
                        except:
                            pass
                        line += pobj.get('pre','') + keydisp + pobj.get('post','') + " "
                if 'default' in pobj:
                    line += pobj.get('default','') + " "
            if line:
                output += line.strip().strip(",") + "<br />"

        if self.get_showkeys():
            output += '<table>'
            keys = [i for i in self.get_showkeys().split(',')]
            for key in keys:
                out = self.get_str(self.set()[counter],key)
                if out:
                    output += '<tr><td><strong>' + key + '</strong>: ' + out + '</td></tr>'
            output += '</table>'
        return output
        
    '''get all currently available keys in ES, and see if they are searchable'''
    def get_keys(self):
        self.seenkey = []
        self.keys = []
        for record in self.set():
            for key in record.keys():
                if key not in self.seenkey:
                    if isinstance(record[key],basestring):
                        self.keys.append({"key":key,"sortable":True})
                    else:
                        if not isinstance(record[key],list):
                            record[key] = [record[key]]
                        for each in record[key]:
                            if isinstance(each,dict):
                                for thing in each.keys():
                                    if key+'.'+thing not in self.seenkey:
                                        if isinstance(each[thing],basestring):
                                            self.keys.append({"key":key+'.'+thing,"sortable":True,"nodisplay":True})
                                        else:
                                            self.keys.append({"key":key+'.'+thing,"sortable":False,"nodisplay":True})
                                        self.seenkey.append(key+'.'+thing)
                                if key not in self.seenkey:
                                    self.keys.append({"key":key,"sortable":False,"nofacet":True})
                                    self.seenkey.append(key)
                            else:
                                if key not in self.seenkey:
                                    self.keys.append({"key":key,"sortable":False})
                                    self.seenkey.append(key)
                    self.seenkey.append(key)
        self.keys.sort(key=lambda x: x['key'])
        return self.keys
    
    '''get keys to show on results'''
    def get_showkeys(self,format="string"):
        if format == "string":
            if not self.showkeys:
                return "";
            return self.showkeys
        else:
            if not self.showkeys:
                return []
            return [i for i in self.showkeys.split(',')]

    def get_showfacets(self,format="string"):
        self.showfacets = ""
        for item in self.args['facet_fields']:
            self.showfacets += item['key'] + ','
        self.showfacets = self.showfacets.strip(',')
        if format == "string":
            return self.showfacets
        else:
            return [i for i in self.showfacets.split(',')]

    def get_rpp_options(self):
        return self.config.results_per_page_options

    def numFound(self):
        return int(self.results['hits']['total'])

    def page_size(self):
        return int(self.args.get("size",10))

    def paging_range(self):
        return ( self.numFound() / self.page_size() ) + 1

    def sorted_by(self):
        if "sort" in self.args:
            return self.args["sort"].keys()[0].replace(self.config.facet_field,"")
        return ""

    def sort_order(self):
        if "sort" in self.args:
            return self.args["sort"][self.args["sort"].keys()[0]]["order"]
        return ""
        
    def start(self):
        return int(self.args.get('start',0))

    def set(self):
        '''Return list of search result items'''
        return [rec['_source'] for rec in self.results['hits']['hits']]


    def get_facet_display_name(self,facetkey):
        for item in self.facets:
            if 'key' in item:
                if item['key'] == facetkey:
                    if 'display_name' in item:
                        return item['display_name']
        return facetkey

    def get_str(self, result, field, raw=False):
        parts = field.split('.')
        if len(parts) == 2:
            res = result.get(parts[0],'')
            if isinstance(res,list):
                res = [i[parts[1]] for i in res]
            elif isinstance(res,dict):
                res = res.get(parts[1],'')
        else:
            res = result.get(field,"")
        if not res:
            return ""
        if self.config.display_value_functions.has_key(field) and not raw:
            d = self.config.display_value_functions[field]
            func_name = d.keys()[0]
            args = d[func_name]
            args["field"] = field
            if self.incollection:
                args["incollection"] = self.incollection
            args["path"] = self.path
            func = globals()[func_name]
            return func(res, args)
        else:
            if isinstance(res,list):
                if isinstance(res[0],dict):
                    out = ""
                    for item in res:
                        if item.get('id','').startswith('http'):
                            theid = '<a href="' + item['id'] + '">' + item['id'] + '</a>'
                        else:
                            theid = item.get('id','')
                        out += item.get('type','') + ": " + theid + "<br />"
                    return out
                else:
                    return ','.join([str(i) for i in res])
            else:
                return res
        return res
        
    def get_meta(self):
        if self.incollection:
            meta = '<p><a href="/'
            meta += self.path + '.json?size=' + str(len(self.incollection))
            meta += '">Download this collection</a><br />'
            meta += 'This collection was created by <a href="/account/' + self.incollection['owner'] + '">' + self.incollection['owner'] + '</a><br />'
            if "source" in self.incollection and self.incollection['source']:
                meta += 'The source of this collection is <a href="'
                meta += self.incollection["source"] + '">' + self.incollection["source"] + '</a>.<br /> '
            if "modified" in self.incollection:
                meta += 'This collection was last updated on ' + self.incollection["modified"] + '. '
            if not self.current_user.is_anonymous() and self.current_user['id'] == self.incollection['owner']:
                if "source" in self.incollection and self.incollection['source']:
                    meta += '<br /><a href="/upload?source=' + self.incollection["source"]
                    meta += '&collection=' + self.incollection['id'] + '">Refresh </a> this collection (overwrites any local changes).'
                meta += '<br /><a href="/collections/' + self.incollection['id']
                meta += '?display_settings=edit">Customise the display</a> of this collection</a>.<br />'
                meta += '<a href="/collections/' + self.incollection['id'] + '">Edit the metadata</a> of this collection.<br />'
                meta += '<a href="/collections/' + self.incollection['id'] + '?delete=true">Delete this collection</a>.'

            return meta
        else:
            return ""

    def get_coll_recordcount(self,collid):
        coll = bibserver.dao.Collection.get(collid)
        if coll:
            return len(coll)
        else:
            return ''

    def get_record_version(self,recordid):
        record = bibserver.dao.Record.get(recordid)
        if not record:
            record = bibserver.dao.Collection.get(recordid)
        return record.version

    def get_record_as_table(self,which=0):
        return self.tablify(self.set()[which])
        
    def tablify(self,thing):
        if not thing:
            return ""
        if isinstance(thing,int):
            thing = str(thing)
        if isinstance(thing,dict):
            print thing
            s = '<table>'
            for key,val in thing.iteritems():
                s += '<tr><td><strong>' + key + '</strong></td><td>' + self.tablify(val) + '</td></tr>'
            s += '</table>'
        elif isinstance(thing,list):
            s = '<table>'
            for item in thing:
                s += '<tr><td>' + self.tablify(item) + '</tr></td>'
            s += '</table>'
        else:
            s = thing
        return s



# the following methods can be called by get_field_display
# to perform various functions upon a field for display

def authorify(vals, dict):
    return ' and '.join(['<a class="author_name" alt="search for ' + i + '" title="search for ' + i + '" ' + 'href="?q=' + i + '">' + i + '</a>' for i in vals])

def doiify(value, dict):
    # dois may start with:
    # 10. - prefix http://dx.doi.org/
    # doi: - strip doi: and replace with http://dx.doi.org/
    # http://dx.doi.org/ already done, just linkify
    resolver = dict.get("resolver", "http://dx.doi.org/")
    link = None
    if value.startswith("10."):
        link = resolver + value
    elif value.startswith("doi:"):
        link = resolver + value[4:]
    elif value.startswith("http://"):
        link = value
    
    if link is not None:
        return '<a href="' + link + '">' + value + '</a>'
    else:
        return value

def collectionify(value, dict):
    # for the given value, make it a link to a collection facet URL
    coll = bibserver.dao.Collection.get(value[0])
    if coll:
        return '<a href="/' + coll['owner'] + "/" + value[0] + '" alt="go to collection '  + value[0] + '" title="go to collection '  + value[0] + '">' + value[0] + '</a>'
    else:
        return value

def bibsoup_links(vals,dict):
    links = ""
    for url in vals:
        links += '<a href="' + url['url'] + '">'
        if 'anchor' in url:
            links += url['anchor']
        else:
            links += url['url']
        if 'format' in url:
            links += ' (' + url['format'] + ') '
        links += '</a> | '
    return links.strip(' | ')

def searchify(value, dict):
    # for the given value, make it a link to a search of the value
    return '<a href="?q=' + value + '" alt="search for ' + value + '" title="search for ' + value + '">' + value + '</a>'

def implicify(value, dict):
    # for the given value, make it a link to an implicit facet URL
    return '<a href="/' + dict.get("field") + "/" + value + '" alt="go to ' + dict.get("field") + " - "  + value + '" title="go to ' + dict.get("field") + " - "  + value + '">' + value + '</a>'

def wrap(value, dict):
    return dict['start'] + value + dict['end']
    
def personify(value, dict):
    # for the given value, make it a link to a person URL
    return '<a href="/person/' + value + '" alt="go to '  + value + ' record" title="go to ' + value + ' record">' + value + '</a>'


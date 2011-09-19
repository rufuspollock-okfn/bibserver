import json, urllib2
from copy import deepcopy
import operator, unicodedata
import bibserver.dao
import bibserver.config

class IOManager(object):
    def __init__(self, results, args):
        self.results = results
        self.config = bibserver.config.Config()
        self.args = args if args is not None else {}
        self.facet_fields = {}
        for facet,data in self.results['facets'].items():
            self.facet_fields[facet.replace(self.config.facet_field,'')] = data["terms"]

    def get_q(self):
        return self.args.get('q','')
    
    def get_safe_terms_object(self):
        terms = {}
        for term in self.args["terms"]:
            if term.replace(self.config.facet_field,'') not in self.args["path"]:
                theterm = '['
                for i in self.args['terms'][term]:
                    theterm += '"' + i + '",'
                theterm = theterm[:-1]
                theterm += ']'
                terms[term.replace(self.config.facet_field,'')] = theterm
        return terms    


    # run the desired method on a field content, to alter it for display
    # see the bottom of this file for the collection of methods to run
    def get_field_display(self, field, value):
        if self.config.display_value_functions.has_key(field):
            d = self.config.display_value_functions[field]
            func_name = d.keys()[0]
            args = d[func_name]
            args["field"] = field
            func = globals()[func_name]
            return func(value, args)
        else:
            return value

    def get_path_params(self,myargs):
        param = '/' + myargs["path"] + '?' if (myargs["path"] != '') else self.config.base_url + '?'
        if 'q' in myargs:
            param += 'q=' + myargs['q'] + '&'
        if 'terms' in myargs:
            for term in myargs['terms']:
                if term.replace(self.config.facet_field,'') not in self.args["path"]:
                    val = '[' + ",".join(urllib2.quote('"{0}"'.format(i.encode('utf-8'))) for i in myargs['terms'][term]) + ']'
                    param += term.replace(self.config.facet_field,'') + '=' + val + '&'
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
            
    def has_values(self, facet):
        return facet in self.config.facet_fields and facet in self.facet_fields

    def get_display_fields(self):
        return self.config.display_fields

    def get_facet_fields(self):
        return self.config.facet_fields

    def get_rpp_options(self):
        return self.config.results_per_page_options

    def get_sort_fields(self):
        return self.config.sort_fields

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

    def get_str(self, result, field, raw=False):
        if result.get(field) is None:
            return ""
        if raw:
            if isinstance(result.get(field), list):
                return " and ".join([val for val in result.get(field)])
            else:
                return result.get(field)
        if isinstance(result.get(field), list):
            if isinstance(result.get(field)[0], dict):
                return result.get(field)
            return " and ".join([self.get_field_display(field, val) for val in result.get(field)])
        elif isinstance(result.get(field), dict):
            return result.get(field)
        else:
            return self.get_field_display(field, result.get(field))
        
    def get_meta(self):
        try:
            if "collection/" in self.args['path']:
                coll = self.results['hits']['hits'][0]["_source"]["collection"]
                if isinstance(coll,list):
                    coll = coll[0]
                res = bibserver.dao.Record.query(q='collection' + self.config.facet_field + ':"' + coll + '" AND type:collection')
                rec = res["hits"]["hits"][0]["_source"]
                sizer = bibserver.dao.Record.query(q='collection' + self.config.facet_field + ':"' + coll + '"')

                print str(sizer["hits"]["total"])
                meta = '<p><a href="/'
                meta += self.args['path'] + '.json?size=' + str(sizer["hits"]["total"])
                meta += '">Download this collection</a><br />'
                if "source" in rec:
                    meta += 'The source of this collection is <a href="'
                    meta += rec["source"] + '">' + rec["source"] + '</a>.<br /> '
                if "received" in rec:
                    meta += 'This collection was last updated on ' + rec["received"] + '. '
                if "source" in rec:
                    meta += '<br />If changes have been made to the source file since then, '
                    meta += '<a href="/upload?source=' + rec["source"] + '&collection=' + rec["collection"]
                    meta += '">refresh this collection</a>.'
                meta += '</p>'
                return meta
            else:
                return ""
        except:
            return ""
        



# the following methods can be called by get_field_display
# to perform various functions upon a field for display

def wrap(value, dict):
    return dict['start'] + value + dict['end']
    
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

def searchify(value, dict):
    # for the given value, make it a link to a search of the value
    return '<a href="?q=' + value + '" alt="search for ' + value + '" title="search for ' + value + '">' + value + '</a>'

def implicify(value, dict):
    # for the given value, make it a link to an implicit facet URL
    return '<a href="/' + dict.get("field") + "/" + value + '" alt="go to ' + dict.get("field") + " - "  + value + '" title="go to ' + dict.get("field") + " - "  + value + '">' + value + '</a>'

def personify(value, dict):
    # for the given value, make it a link to a person URL
    return '<a href="/person/' + value + '" alt="go to '  + value + ' record" title="go to ' + value + ' record">' + value + '</a>'

def _get_location_pairs(message, start_sub, finish_sub):
    idx = 0
    pairs = []
    while message.find(start_sub, idx) > -1:
        si = message.find(start_sub, idx)
        sf = message.find(finish_sub, si)
        pairs.append((si, sf))
        idx = sf
    return pairs

def _create_url(url):
    return "<a href=\"%(url)s\">%(url)s</a>" % {"url" : url}

def linkify(nm, args):
    parts = _get_location_pairs(nm, "http://", " ")
    
    # read into a sortable dictionary
    dict = {}
    for (s, f) in parts:
        dict[s] = f
    
    # sort the starting points
    keys = dict.keys()
    keys.sort()
    
    # determine the splitting points
    split_at = [0]
    for s in keys:
        f = dict.get(s)
        split_at.append(s)
        split_at.append(f)
    
    # turn the splitting points into pairs
    pairs = []
    for i in range(0, len(split_at)):
        if split_at[i] == -1:
            break
        if i + 1 >= len(split_at):
            end = len(nm)
        elif split_at[i+1] == -1:
            end = len(nm)
        else:
            end = split_at[i+1]
        pair = (split_at[i], end)
        pairs.append(pair)
    
    frags = []
    for s, f in pairs:
        frags.append(nm[s:f])
    
    for i in range(len(frags)):
        if frags[i].startswith("http://"):
            frags[i] = _create_url(frags[i])
    
    message = "".join(frags)
    return message



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
        self.facet_counts = {
            'facet_fields': {}
            }
        for facet,data in self.results['facets'].items():
            facet = facet.replace(self.config.facet_field,'')
            self.facet_counts['facet_fields'][facet] = {}
            for termdict in data['terms']:
                self.facet_counts['facet_fields'][facet][termdict['term']] = termdict['count']

    def get_q(self):
        return self.args.get('q','')
    
    def get_safe_terms_object(self):
        terms = {}
        for term in self.args["terms"]:
            if term.replace(self.config.facet_field,'') not in self.args["path"]:
                terms[term.replace(self.config.facet_field,'')] = '[' + ','.join('"{0}"'.format(i) for i in self.args['terms'][term]) + ']'                                
        return terms    

    
    def get_display_fields(self):
        return self.config.display_fields

    def get_facet_fields(self):
        return self.config.facet_fields

    def get_facet_display(self, facet_name):
        return facet_name
    
    # run the desired method on a field content, to alter it for display
    def get_field_display(self, field, value):
        if self.config.display_value_functions.has_key(field):
            d = self.config.display_value_functions[field]
            func_name = d.keys()[0]
            args = d[func_name]
            args["field"] = field
            func = globals()[func_name]
            return func(str(value), args)
        else:
            return value

    def get_rpp_options(self):
        return self.config.results_per_page_options

    def get_path_params(self,myargs):
        param = '/' + myargs["path"] + '?' if (myargs["path"] != '') else self.config.base_url + '?'
        if 'q' in myargs:
            param += 'q=' + myargs['q'] + '&'
        if 'terms' in myargs:
            for term in myargs['terms']:
                if term.replace(self.config.facet_field,'') not in self.args["path"]:
                    val = '[' + ",".join(urllib2.quote('"{0}"'.format(i)) for i in myargs['terms'][term]) + ']'
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
            field  += self.config.facet_field
            myargs['terms'][field].remove(value)
            if len(myargs['terms'][field]) == 0:
                del myargs['terms'][field]
        else:
            del myargs['terms'][field]
        return self.get_path_params(myargs)


    def get_ordered_facets(self, facet):
        if facet in self.config.facet_fields:
            return sorted(self.facet_counts['facet_fields'][facet].iteritems(), key=operator.itemgetter(1), reverse=True)

    def in_args(self, facet, value=None):
        if value is not None:
            return self.args['terms'].has_key(facet + self.config.facet_field) and value in self.args['terms'][facet + self.config.facet_field]
        else:
            return self.args['terms'].has_key(facet)
            
    def has_values(self, facet):
        if facet in self.config.facet_fields:
            print len(self.facet_counts['facet_fields'][facet])
            return len(self.facet_counts['facet_fields'][facet]) > 0
        return False

    def numFound(self):
        return int(self.results['hits']['total'])

    def set(self):
        '''Return list of search result items'''
        return [rec['_source'] for rec in self.results['hits']['hits']]

    def page_size(self):
        return int(self.args.get("size",10))

    def start(self):
        return int(self.args.get('start',0))

    def get_str(self, result, field, raw=False):
        if result.get(field) is None:
            return ""
        if raw:
            if hasattr(result.get(field), "append"):
                return ", ".join([val for val in result.get(field)])
            else:
                return result.get(field)
        if hasattr(result.get(field), "append"):
            return ", ".join([self.get_field_display(field, val) for val in result.get(field)])
        else:
            return self.get_field_display(field, result.get(field))
        
    def get_meta(self):
        try:
            coll = self.results['hits']['hits'][0]["_source"]["collection"]
            if isinstance(coll,list):
                coll = coll[0]
            res = bibserver.dao.Record.query(q='collection:' + coll + ' AND type:collection')
            rec = res["hits"]["hits"][0]["_source"]
            meta = "<p>"
            if "source" in rec:
                meta = 'The source of this collection is <a href="'
                meta += rec["source"] + '">' + rec["source"] + '</a>. '
            if "received" in rec:
                meta += 'This collection was last updated on ' + rec["received"] + '. '
            if "source" in rec:
                meta += '<br />If changes have been made to the source file since then, '
                meta += '<a href="/upload?source=' + rec["source"] + '&collection=' + rec["collection"]
                meta += '">refresh this collection</a>.'
            meta += '</p>'
            return meta
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



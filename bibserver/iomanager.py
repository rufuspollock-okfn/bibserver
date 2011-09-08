import json, urllib2
from copy import deepcopy
import operator, unicodedata
import bibserver.dao

class IOManager(object):
    def __init__(self, results, config, args):
        self.results = results
        self.config = config
        self.args = args if args is not None else {}
        self.facet_counts = {
            'facet_fields': {}
            }
        for facet,data in self.results['facets'].items():
            self.facet_counts['facet_fields'][facet] = {}
            for termdict in data['terms']:
                self.facet_counts['facet_fields'][facet][termdict['term']] = termdict['count']

    def get_param(self,myargs):
        param = '?'
        if 'q' in myargs:
            param += 'q=' + myargs['q'] + '&'
        if 'terms' in myargs:
            for term in myargs['terms']:
                val = '[' + ",".join(urllib2.quote('"{0}"'.format(i)) for i in myargs['terms'][term]) + ']'
                param += term + '=' + val + '&'
        return param

    def get_add_url(self, field, value):
        myargs = deepcopy(self.args)
        if myargs['terms'].has_key(field):
            if value not in myargs['terms'][field]:
                myargs['terms'][field].append(value)
        else:
            myargs['terms'][field] = [value]
        return self.config.base_url + self.get_param(myargs)
        
    def get_delete_url(self, field, value=None):
        myargs = deepcopy(self.args)
        if value is not None:
            myargs['terms'][field].remove(value)
            if len(myargs['terms'][field]) == 0:
                del myargs['terms'][field]
        else:
            del myargs['terms'][field]
        return self.config.base_url + self.get_param(myargs)


    def get_ordered_facets(self, facet):
        if facet in self.config.facet_fields:
            return sorted(self.facet_counts['facet_fields'][facet].iteritems(), key=operator.itemgetter(1), reverse=True)

    def in_args(self, facet, value=None):
        if value is not None:
            return self.args['terms'].has_key(facet) and value in self.args['terms'][facet]
        else:
            return self.args['terms'].has_key(facet)
            
    def has_values(self, facet):
        if facet in self.config.facet_fields:
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
            return ", ".join([self.config.get_field_display(field, val) for val in result.get(field)])
        else:
            return self.config.get_field_display(field, result.get(field))
        
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
        


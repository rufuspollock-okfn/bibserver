import operator, unicodedata
import bibserver.config 


class ResultManager(object):
    def __init__(self, results, config, args):
        self.results = results
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()
        # TODO: set from query args properly rather than hardcode
        self.start = 0
        self.facet_counts = {
            'facet_fields': {}
            }
        for facet,data in self.results['facets'].items():
            self.facet_counts['facet_fields'][facet] = {}
            for termdict in data['terms']:
                self.facet_counts['facet_fields'][facet][termdict['term']] = termdict['count']

    def get_ordered_facets(self, facet):
        if facet in self.config.facet_fields:
            return self._sort_facets_by_count(self.facet_counts['facet_fields'][facet])
    
    def in_args(self, facet, value=None):
        if value is not None:
            return self.args['q'].has_key(facet) and value in self.args['q'][facet]
        else:
            return self.args['q'].has_key(facet)
            
    def get_search_constraints(self):
        return self.args['q']
            
    def has_values(self, facet):
        if facet in self.config.facet_fields:
            return len(self.facet_counts['facet_fields'][facet]) > 0
        return False

    def is_start(self):
        return True
        
    def is_end(self):
        return True

    def set_size(self):
        return len(self.results['hits']['hits'])

    def numFound(self):
        return int(self.results['hits']['total'])

    def set(self):
        '''Return list of search result items'''
        return [rec['_source'] for rec in self.results['hits']['hits']]

    def start_offset(self, off):
        return self.start + off

    def finish(self):
        return self.start + self.set_size()

    def page_size(self):
        return self.args['rows']

    def get_str(self, result, field):
        if result.get(field) is None:
            return ""
        if hasattr(result.get(field), "append"):
            return ", ".join([self.asciify(self.config.get_field_display(field, val)) for val in result.get(field)])
        else:
            return self.asciify(self.config.get_field_display(field, result.get(field)))
    
    def asciify(self, string):
        # this causes errors
        decoded = string.decode('latin-1')
        return unicodedata.normalize('NFKD', unicode(decoded)).encode('ascii','ignore')
    
    def first_page_end(self):
        return self.args['rows']
    
    def last_page_start(self):
        return self.results.numFound - (self.results.numFound % self.args['rows'])
        
    def get_previous(self, num):
        pairs = []
        for i in range(num + 1, 0, -1):
            first = self.start - (self.args['rows'] * i)
            if first >= self.args['rows']: # i.e. greater than the first page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def get_next(self, num):
        pairs = []
        for i in range(1, num + 1):
            first = self.start + (self.args['rows'] * i)
            last_page_size = self.numFound() % self.args['rows']
            if first + self.args['rows'] <= self.numFound() - last_page_size: # i.e. less than the last page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def _sort_facets_by_count(self, dict):
        return sorted(dict.iteritems(), key=operator.itemgetter(1), reverse=True)


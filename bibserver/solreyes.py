from StringIO import StringIO
from copy import deepcopy
from pkg_resources import resource_stream
from datetime import datetime, timedelta
import os, json, urllib2, operator, re, unicodedata

import solr
from mako.template import Template
from mako.runtime import Context
from mako.lookup import TemplateLookup

from flask.views import View
from flask import Blueprint, current_app
from flask import request, url_for, g, send_file
from flaskext.mako import render_template

import bibserver.config 

solreyes_app = Blueprint('bibserver', __name__)


class ESResultManager(object):
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
        return unicodedata.normalize('NFKD', unicode(string)).encode('ascii','ignore')
    
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
        

        
class UrlManager(object):
    def __init__(self, config, args, implicit_facets):
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()
        self.implicit_facets = implicit_facets
        self.base_args = self.strip_implicit_facets()
    
    def strip_implicit_facets(self):
        myargs = deepcopy(self.args)
        if self.implicit_facets is None:
            return myargs
        if not self.args.has_key('q'):
            return myargs
        
        for field in self.implicit_facets.keys():
            if myargs['q'].has_key(field):
                del myargs['q'][field]
        return myargs
    
    def get_search_form_action(self):
        return self.config.base_url
    
    def get_form_field_args(self):
        myargs = deepcopy(self.base_args)
        if myargs.has_key("search"):
            del myargs['search']
        j = json.dumps(myargs)
        return urllib2.quote(j)
    
    def get_add_url(self, field, value, upper=None):
        myargs = deepcopy(self.base_args)
        if myargs["q"].has_key(field):
            if upper is None and value not in myargs["q"][field]:
                myargs["q"][field].append(value)
            elif upper is not None:
                myargs["q"][field] = [value, upper]
        else:
            if upper is None:
                myargs["q"][field] = [value]
            else:
                myargs["q"][field] = [value, upper]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_add_date_url(self, field, value, upper=None):
        myargs = deepcopy(self.base_args)
        value = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(value, '02')
        if upper is not None and upper != -1:
            upper = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(upper, '02')
        if myargs["q"].has_key(field):
            if upper is None and value not in myargs["q"][field]:
                myargs["q"][field].append(value)
            elif upper is not None:
                myargs["q"][field] = [value, upper]
        else:
            if upper is None:
                myargs["q"][field] = [value]
            else:
                myargs["q"][field] = [value, upper]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)

    def get_delete_url(self, field, value=None):
        myargs = deepcopy(self.base_args)
        if value is not None:
            myargs['q'][field].remove(value)
            if len(myargs['q'][field]) == 0:
                del myargs['q'][field]
        else:
            del myargs['q'][field]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_position_url(self, position):
        myargs = deepcopy(self.base_args)
        myargs["start"] = position
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_rpp_url(self, rpp):
        myargs = deepcopy(self.base_args)
        myargs["rows"] = int(rpp)
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_sort_url(self, field, direction):
        myargs = deepcopy(self.base_args)
        if myargs.has_key("sort"):
            isnew = True
            for i in range(len(myargs['sort'])):
                f, d = myargs['sort'][i]
                if f == field:
                    myargs['sort'][i] = [field, direction]
                    isnew = False
                    break
            if isnew:
                myargs['sort'].append([field, direction])
        else:
            myargs["sort"] = [[field, direction]]
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_unsort_url(self, field):
        myargs = deepcopy(self.base_args)
        for i in range(len(myargs['sort'])):
            f, direction = myargs['sort'][i]
            if f == field:
                del myargs['sort'][i]
                break
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        

class Configuration(object):
    def __init__(self, configuration_dict):
        '''Create Configuration object from a configuration dictionary.'''
        self.cfg = configuration_dict
        
        # build a map for display of fields
        self.facet_display_values = {}
        for field, props in self.cfg['facet_fields'].iteritems():
            self.facet_display_values[field] = props["display"]
        
    def __getattr__(self, attr):
        return self.cfg.get(attr, None)
        
    def get_facet_display(self, facet_name):
        return self.facet_display_values.get(facet_name, facet_name)
        
    def get_default_args(self):
        fields = deepcopy(self.facet_fields.keys())
        return {
            "q" : {},
            "start" : 0,
            "facet_field" : fields,
            "rows" : self.default_results_per_page
        }
        
    def get_value_display(self, facet, value):
        return value
            
    def get_field_display(self, field, value):
        if self.display_value_functions.has_key(field):
            d = self.display_value_functions[field]
            func_name = d.keys()[0]
            args = d[func_name]
            args["field"] = field #----MM
            func = globals()[func_name]
            return func(str(value), args)
        else:
            return value
                        
    def get_field_name(self, field):
        return self.display_fields.get(field, field)
        
    def display_upper(self, facet, lower, upper):
        if self.upper_display_functions.has_key(facet):
            d = self.upper_display_functions[facet]
            func_name = d.keys()[0]
            args = d[func_name]
            func = globals()[func_name]
            return func(lower, upper, args)
        else:
            return True
            

def value_map(value, d):
    return d.get(value, value)

def regex_map(value, dict):
    capture = re.findall(dict["expression"], value)
    if len(capture) == 1:
        return capture[0]
    return value
    
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

def years_different(lower, upper, dict):
    lyear = regex_map(lower, {"expression" : "([\\d]{4})-.*"})
    uyear = regex_map(upper, {"expression" : "([\\d]{4})-.*"})
    return lyear != uyear

def date_range_count(args, result, dict):
    if not args['q'].has_key(dict['bounding_field']):
        values = result.get(dict['results_field'])
        if values is not None:
            return str(len(values))
        else:
            return 0
    start, end = args['q'][dict['bounding_field']]
    sdate = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    edate = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    values = result.get(dict['results_field'])
    if values is None:
        return 0
    count = 0
    for vdate in values:
        # convert to offset aware datetime
        strdate = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(vdate, '02')
        vdate = datetime.strptime(strdate, "%Y-%m-%dT%H:%M:%SZ")
        if vdate >= sdate and vdate <= edate:
            count += 1
    return str(count)
    
def array_count(args, result, dict):
    values = result.get(dict['count_field'])
    if values is None:
        return 0
    return len(values)
    

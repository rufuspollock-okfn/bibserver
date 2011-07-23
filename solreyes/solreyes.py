import web, solr, os, json, urllib2, operator, re, unicodedata
from mako.template import Template
from mako.runtime import Context
from mako.lookup import TemplateLookup
from StringIO import StringIO
from copy import deepcopy
from pkg_resources import resource_stream
from datetime import datetime, timedelta

class SolrEyesController(object):
    def GET(self):
        # get the args (if available) out of the request
        a = web.input().get("a")
        args = None
        if a is not None:
            a = urllib2.unquote(a)
            args = json.loads(a)
        
        # set up the configuration and the UI properties
        config = Configuration()
        properties = {}
        properties['config'] = config
        
        # if the args are none, then get the default ones from the config
        # FIXME: this is going to generate large URLs, so we probably want
        # a better approach in the long run
        
        initial_request = False
        if args is None:
            args = config.get_default_args()
            initial_request = True
        
        # set the UrlManager for the UI to use
        properties['url_manager'] = UrlManager(config, args)
        
        # create a solr connection and get the results back
        s = Solr(config)
        if initial_request:
            properties['results'] = ResultManager(s.initial(args), config, args)
        else:
            properties['results'] = ResultManager(s.search(args), config, args)
        return self.render(config.template, properties)
    
    def render(self, template_name, properties):
        res_path = os.path.join(os.path.dirname(__file__), 'templates')
        fn = os.path.join(res_path, template_name)
        mylookup = TemplateLookup(directories=[res_path])
        t = Template(filename=fn, lookup=mylookup)
        buf = StringIO()
        ctx = Context(buf, c=properties)
        t.render_context(ctx)
        return buf.getvalue()

class ResultManager(object):
    def __init__(self, results, config, args):
        self.results = results
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()

    def current_sort_order(self):
        if not self.args.has_key('sort'):
            return []
        return self.args['sort']
    
    def current_sort_fields(self):
        if not self.args.has_key('sort'):
            return []
        return [k for k, v in self.args['sort']]

    def get_ordered_facets(self, facet):
        if facet in self.config.facet_fields:
            return self._sort_facets_by_count(self.results.facet_counts['facet_fields'][facet])
        elif facet in self.config.facet_ranges.keys():
            dict = self._get_range_dict(facet)
            return self._sort_facets_by_range(dict)
        elif facet in self.config.facet_dates.keys():
            dict = self._get_date_dict(facet)
            return self._sort_facets_by_range(dict)
    
    def in_args(self, facet, value=None):
        if value is not None:
            return self.args['q'].has_key(facet) and value in self.args['q'][facet]
        else:
            return self.args['q'].has_key(facet)
            
    def get_search_constraints(self):
        return self.args['q']
            
    def get_selected_range_start(self, facet):
        return self.args["q"][facet][0]
    
    def get_selected_range_end(self, facet):
        return self.args["q"][facet][1]
    
    def has_values(self, facet):
        if facet in self.config.facet_fields:
            return len(self.results.facet_counts['facet_fields'][facet]) > 0
        elif facet in self.config.facet_ranges.keys():
            return len(self.results.facet_counts['facet_ranges'][facet]["counts"]) > 0
        elif facet in self.config.facet_dates.keys():
            return len(self.results.facet_counts['facet_dates'][facet]) > 0
        return False
    
    def is_start(self):
        return self.results.start == 0
        
    def is_end(self):
        return self.results.start + self.args['rows'] >= self.results.numFound
    
    def start(self):
        return self.results.start
        
    def finish(self):
        return self.results.start + self.set_size()
        
    def start_offset(self, off):
        return self.results.start + off
        
    def set_size(self):
        return len(self.results.results)
        
    def numFound(self):
        return self.results.numFound
        
    def set(self):
        return self.results.results
    
    def page_size(self):
        return self.args['rows']
    
    def get_str(self, result, field):
        if field in self.config.dynamic_fields.keys():
            return self.config.get_dynamic_value(self.args, result, field)
        
        if result.get(field) is None and field not in self.config.dynamic_fields.keys():
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
            first = self.results.start - (self.args['rows'] * i)
            if first >= self.args['rows']: # i.e. greater than the first page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def get_next(self, num):
        pairs = []
        for i in range(1, num + 1):
            first = self.results.start + (self.args['rows'] * i)
            last_page_size = self.results.numFound % self.args['rows']
            if first + self.args['rows'] <= self.results.numFound - last_page_size: # i.e. less than the last page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def _get_range_dict(self, facet):
        dict = self.results.facet_counts['facet_ranges'][facet]["counts"]
        keys = [int(key) for key in dict.keys()]
        keys.sort()
        rdict = {}
        for i in range(len(keys)):
            lower = int(keys[i])
            upper = -1
            if i < len(keys) - 1:
                upper = int(keys[i+1] - 1)
            r = (lower, upper)
            rdict[r] = dict[str(lower)]
        return rdict
        
    def _get_date_dict(self, facet):
        dict = self.results.facet_counts['facet_dates'][facet]
        keys = [(datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ"), d) for d in dict.keys() if d[0:2].isdigit()]
        keys = sorted(keys, key=operator.itemgetter(0))
        rdict = {}
        for i in range(len(keys)):
            lower, sl = keys[i]
            upper = -1
            if i < len(keys) - 1:
                upper, su = keys[i+1]
                upper = upper - timedelta(seconds=1)
            r = (lower, upper)
            rdict[r] = dict[sl]
        return rdict
    
    def _sort_facets_by_count(self, dict):
        return sorted(dict.iteritems(), key=operator.itemgetter(1), reverse=True)
        
    def _sort_facets_by_range(self, dict):
        # dict = {(a, b) : c, ....} ; we want to sort by a
        # first, cast the dict to tuples
        tups = [(a, b, dict[(a, b)]) for a, b in dict.keys()]
        return sorted(tups, key=operator.itemgetter(0))
        
class UrlManager(object):
    def __init__(self, config, args):
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()
    
    def get_add_url(self, field, value, upper=None):
        myargs = deepcopy(self.args)
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
        myargs = deepcopy(self.args)
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
        myargs = deepcopy(self.args)
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
        myargs = deepcopy(self.args)
        myargs["start"] = position
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_rpp_url(self, rpp):
        myargs = deepcopy(self.args)
        myargs["rows"] = int(rpp)
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_sort_url(self, field, direction):
        myargs = deepcopy(self.args)
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
        myargs = deepcopy(self.args)
        for i in range(len(myargs['sort'])):
            f, direction = myargs['sort'][i]
            if f == field:
                del myargs['sort'][i]
                break
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
class Solr(object):
    def __init__(self, config):
        self.config = config
        self.solr = solr.Solr(self.config.solr_url)
        self.select = solr.SearchHandler(self.solr, self.config.request_handler, arg_separator="__")

    def search(self, args):
        return self._do_query(args)
        
    def initial(self, args):
        args = deepcopy(args)
        args["q"]["*"] = "*"
        args["rows"] = 0
        return self._do_query(args)
        
    def _do_query(self, args, arg_separator="__"):
        # we build all our solr args in one dictionary for convenience
        solr_args = {}
        solr_args['facet'] = "on"
        
        # Except the fields required explicitly by the solrpy api:
        
        #def __call__(self, q=None, fields=None, highlight=None,
        #         score=True, sort=None, sort_order="asc", **params):
        
        # do q separately
        qs = []
        for field in args['q'].keys():
            if field in self.config.facet_fields:
                for value in args['q'][field]:
                    qs.append(field + ":\"" + value + "\"")
            elif field in self.config.facet_ranges.keys():
                limit = args['q'][field][1]
                if limit == -1:
                    limit = self.config.facet_ranges[field]["infinity"]
                qs.append(field + ":[" + str(args["q"][field][0]) + " TO " + str(limit) + "]")
            elif field in self.config.facet_dates.keys():
                limit = args['q'][field][1]
                if limit == -1:
                    now = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
                    limit = self.config.facet_dates[field].get("inifinity", now)
                qs.append(field + ":[" + str(args["q"][field][0]) + " TO " + str(limit) + "]")
            elif field == "*":
                for value in args['q'][field]:
                    qs.append(field + ":" + value)
        q = " AND ".join(qs)
        
        # start position (for paging)
        if args.has_key("start"):
            solr_args["start"] = args["start"]
        
        # set up the ranged search parameters
        for f in args["facet_range"].keys():
            if solr_args.has_key("facet.range"):
                solr_args["facet.range"].append(f)
            else:
                solr_args["facet.range"] = [f]
            
            if args["facet_range"][f].has_key("mincount"):
                solr_args["f." + f + ".facet.mincount"] = args["facet_range"][f]["mincount"]
            
            if args["facet_range"][f].has_key("min"):
                solr_args["f." + f + ".facet.range.start"] = args["facet_range"][f]["min"]
                
            if args["facet_range"][f].has_key("max"):
                solr_args["f." + f + ".facet.range.end"] = args["facet_range"][f]["max"]
                
            if args["facet_range"][f].has_key("gap"):
                solr_args["f." + f + ".facet.range.gap"] = args["facet_range"][f]["gap"]
        
        # set up the date range parameters
        for f in args["facet_date"].keys():
            if solr_args.has_key("facet.date"):
                solr_args["facet.date"].append(f)
            else:
                solr_args["facet.date"] = [f]
            
            if args["facet_date"][f].has_key("mincount"):
                solr_args["f." + f + ".facet.mincount"] = args["facet_date"][f]["mincount"]
            
            if args["facet_date"][f].has_key("min"):
                solr_args["f." + f + ".facet.date.start"] = args["facet_date"][f]["min"]
                
            if args["facet_date"][f].has_key("max"):
                solr_args["f." + f + ".facet.date.end"] = args["facet_date"][f]["max"]
            else:
                solr_args["f." + f + ".facet.date.end"] = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
                
            if args["facet_date"][f].has_key("gap"):
                solr_args["f." + f + ".facet.date.gap"] = args["facet_date"][f]["gap"]
        
        # set up the facet queries
        if args.has_key('facet_query'):
            for f in args['facet_query'].keys():
                if not solr_args.has_key("facet.query"):
                    solr_args["facet.query"] = []
                for q in args['facet_query'][f]['queries']:
                    solr_args["facet.query"].append(f + ":" + q['query'])
        
        # facet mincount from config
        solr_args["facet.mincount"] = self.config.facet_mincount
        
        # number of rows to return
        if args.has_key("rows"):
            solr_args["rows"] = args["rows"]
            
        # plain facet fields
        solr_args["facet.field"] = args["facet_field"]
        
        # sort options
        if args.has_key("sort"):
            sort_parts = []
            for sort_field, direction in args['sort']:
                sort_parts.append(sort_field + " " + direction)
            solr_args["sort"] = ", ".join(sort_parts)
        
        # solrpy convert the keywordargs
        solrpy_args = self.solrpyise(solr_args, arg_separator)
        
        results = self.select(q=q, **solrpy_args)
        return results
    
    def solrpyise(self, dict, arg_separator="__"):
        edict = {}
        for key in dict.keys():
            ekey = self.esc(key, arg_separator)
            edict[str(ekey)] = dict[key]
        return edict
    
    def esc(self, solr_field, arg_separator="__"):
        return solr_field.replace(".", arg_separator)

class Configuration(object):
    def __init__(self):
        # extract the configuration from the json object
        f = resource_stream(__name__, 'config.json')
        c = ""
        for line in f:
            if line.strip().startswith("#"):
                continue
            else:
                c += line
        self.cfg = json.loads(c)
        
        # build a map for display of fields
        self.facet_display_values = {}
        for field, props in self.cfg['facet_fields'].iteritems():
            self.facet_display_values[field] = props["display"]
        for field, props in self.cfg['facet_ranges'].iteritems():
            self.facet_display_values[field] = props["display"]
        for field, props in self.cfg['facet_dates'].iteritems():
            self.facet_display_values[field] = props["display"]
        
    def __getattr__(self, attr):
        return self.cfg.get(attr, None)
        
    def get_facet_display(self, facet_name):
        return self.facet_display_values.get(facet_name, facet_name)
        
    def get_default_args(self):
        fields = deepcopy(self.facet_fields.keys())
        ranges = deepcopy(self.facet_ranges)
        dates = deepcopy(self.facet_dates)
        queries = deepcopy(self.facet_queries)
        for k, v in ranges.iteritems():
            del v['display']
        for k, v in dates.iteritems():
            del v['display']
        for k, v in queries.iteritems():
            del v['display']
        return {
            "q" : {},
            "start" : 0,
            "facet_field" : fields,
            "facet_range" : ranges,
            "facet_date" : dates,
            "rows" : self.default_results_per_page
        }
        
    def get_value_display(self, facet, value):
        if self.facet_value_functions.has_key(facet):
            d = self.facet_value_functions[facet]
            func_name = d.keys()[0]
            args = d[func_name]
            func = globals()[func_name]
            return func(value, args)
        else:
            return value
            
    def get_field_display(self, field, value):
        if self.display_value_functions.has_key(field):
            d = self.display_value_functions[field]
            func_name = d.keys()[0]
            args = d[func_name]
            func = globals()[func_name]
            return func(str(value), args)
        else:
            return value
            
    def get_dynamic_value(self, args, result, field):
        if self.dynamic_fields.has_key(field):
            d = self.dynamic_fields[field]
            func_name = d.keys()[0]
            fargs = d[func_name]
            func = globals()[func_name]
            return func(args, result, fargs)
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
            
    def is_range(self, facet):
        return facet in self.facet_ranges.keys()
        
    def is_date_range(self, facet):
        return facet in self.facet_dates.keys()

def value_map(value, d):
    return d.get(value, value)

def regex_map(value, dict):
    capture = re.findall(dict["expression"], value)
    if len(capture) == 1:
        return capture[0]
    return value

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
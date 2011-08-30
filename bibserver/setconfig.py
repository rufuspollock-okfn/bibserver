from copy import deepcopy

import bibserver.config


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
            args["field"] = field
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
            

# the following methods probably no longer belong in here - should be in resultmanager, I think

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
    

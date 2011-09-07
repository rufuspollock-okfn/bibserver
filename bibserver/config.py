import json

'''read the config.json file and make available as a config dict'''

def load_config(path):
    fileobj = open(path)
    c = ""
    for line in fileobj:
        if line.strip().startswith("#"):
            continue
        else:
            c += line
    out = json.loads(c)

    out["facet_fields_display"] = {}
    for item in out["facet_fields"]:
        out["facet_fields_display"][item + out["facet_field"]] = item
    out["facet_fields"] = [field + out["facet_field"] for field in out["facet_fields"]]

    return out

config = load_config('config.json')

__all__ = ['config']


''' wrap a config dict in a class and provide methods for displaying fields'''

class Config(object):
    def __init__(self,confdict):
        '''Create Configuration object from a configuration dictionary.'''
        self.cfg = confdict
        
    def __getattr__(self, attr):
        return self.cfg.get(attr, None)
        
    def get_facet_display(self, facet_name):
        if self.facet_fields_display.has_key(facet_name):
            return self.facet_fields_display[facet_name]
        else:
            return facet_name
    
    # run the desired method on a field content, to alter it for display
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



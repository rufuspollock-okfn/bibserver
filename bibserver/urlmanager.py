from copy import deepcopy
import json, urllib2
import bibserver.config 

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


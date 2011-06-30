import json

class JsonSerialiser(object):
    def serialise(self, bibdataset):
        return json.dumps(bibdataset.datalist)

import json

class JSONLDParser(object):

    def __init__(self):
        pass
        
    def parse(self, fileobj):
        data = json.load(fileobj)
        records = data.get('@',[])
        for item in records:
            # do stuff to convert to 
            pass
        if '#' in data:
            metadata = {"namespaces": data['#']}
        else:
            metadata = {}
        return records, metadata



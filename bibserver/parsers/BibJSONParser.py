import json

class BibJSONParser(object):

    def __init__(self):
        pass
        
    def parse(self, fileobj):
        data = json.load(fileobj)
        records = data.get("records",[])
        metadata = data.get("metadata",{})
        return records, metadata



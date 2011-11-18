import json

class JSONParser(object):

    def __init__(self):
        pass
        
    def parse(self, fileobj):
        incoming = json.load(fileobj)

        # check if the incoming is bibjson
        if 'records' in incoming:
            data = incoming['records']
            metadata = incoming.get('metadata',{})
        else:
            data = incoming
            metadata = {}
    
        return data, metadata



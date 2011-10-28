import json

class JSONParser(object):

    def __init__(self):
        pass
        
    def parse(self, fileobj):
        data = json.load(fileobj)
        return data, {}



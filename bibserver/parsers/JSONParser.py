import json
from bibserver.parsers import BaseParser

class JSONParser(BaseParser):

    def parse(self):
        incoming = json.load(self.fileobj)

        if 'records' in incoming:
            # if the incoming is bibjson, get records and metadata
            data = self.customisations(incoming['records'])
            metadata = incoming.get('metadata',{})
        else:
            data = incoming
            metadata = {'schema':'v0.81'}
    
        return data, metadata

    def customisations(self,records):
        for record in records:
            # tidy any errant authors as strings
            if 'author' in record:
                if ' and ' in record['author']:
                    record['author'] = record['author'].split(' and ')
            # do any conversions to objects
        return records


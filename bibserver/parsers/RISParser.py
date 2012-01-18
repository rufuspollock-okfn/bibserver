'''this file can be called as a module or called directly from the command line like so:

python RISParser.py /path/to/file.txt
Returns a list of record dicts

Details of the RIS format
http://en.wikipedia.org/wiki/RIS_%28file_format%29
'''

FIELD_MAP = {
    'TY' : 'type',
    'TI' : 'title',
    'AU' : 'author',
}
VALUE_MAP = {
    'AU' : lambda v: [{u'name':vv.decode('utf8')} for vv in v]
}
DEFAULT_VALUE_FUNC = lambda v: u' '.join(vv.decode('utf8') for vv in v)

from bibserver.parsers import BaseParser

class RISParser(BaseParser):
    def __init__(self, fileobj):
        super(RISParser, self).__init__(fileobj)
        self.data = []
        
    def add_chunk(self, chunk):
        if not chunk: return
        tmp = {}
        for k,v in chunk.items():
            tmp[FIELD_MAP.get(k, k)] =  VALUE_MAP.get(k, DEFAULT_VALUE_FUNC)(v)   
        self.data.append(tmp)
        
    def parse(self):
        data, chunk = [], {}
        for line in self.fileobj:
            line = line.strip()
            if not line: continue
            parts = line.split('  - ')
            if len(parts) < 2: continue
            field = parts[0]
            if field == 'TY':
                self.add_chunk(chunk)
                chunk = {}
            value = '  - '.join(parts[1:])
            if value:
                chunk.setdefault(field, []).append(value)        
        self.add_chunk(chunk)
        return self.data, {}
        
# in case file is run directly
if __name__ == "__main__":
    import sys, json
    fileobj = open(sys.argv[1])
    parser = RISParser(fileobj)
    data, metadata = parser.parse()
    sys.stdout.write(json.dumps(data, indent=2))

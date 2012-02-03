'''this file can be called as a module or called directly from the command line like so:

python RISParser.py /path/to/file.txt
Returns a list of record dicts

Details of the RIS format
http://en.wikipedia.org/wiki/RIS_%28file_format%29
'''

FIELD_MAP = {
    "DO": "doi", 
    "SP": "pages", 
    "M2": "start page", 
    "DB": "name of database", 
    "DA": "date", 
    "M1": "number", 
    "M3": "type", 
    "N1": "notes", 
    "ST": "short title", 
    "DP": "database provider", 
    "CN": "call number", 
    "IS": "number", 
    "LB": "label", 
    "TA": "translated author", 
    "TY": "type ", 
    "UR": "url", 
    "TT": "translated title", 
    "PY": "year", 
    "PB": "publisher", 
    "A3": "tertiary author", 
    "C8": "custom 8", 
    "A4": "subsidiary author", 
    "TI": "title", 
    "C3": "custom 3", 
    "C2": "pmcid", 
    "C1": "note", 
    "C7": "custom 7", 
    "C6": "nihmsid", 
    "C5": "custom 5", 
    "C4": "custom 4", 
    "AB": "note", 
    "AD": "institution", 
    "VL": "volume", 
    "CA": "caption", 
    "T2": "secondary title", 
    "T3": "tertiary title", 
    "AN": "accession number", 
    "L4": "figure", 
    "NV": "number of volumes", 
    "AU": "author", 
    "RP": "reprint edition", 
    "L1": "file attachments", 
    "ET": "epub date", 
    "A2": "author", 
    "RN": "note", 
    "LA": "language", 
    "CY": "place published", 
    "J2": "alternate title", 
    "RI": "reviewed item", 
    "KW": "keyword", 
    "SN": "issn", 
    "Y2": "access date", 
    "SE": "section", 
    "OP": "original publication",
    "JF": "journal",
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
        last_field = None
        for line in self.fileobj:
            if line.startswith(' ') and last_field:
                chunk.setdefault(last_field, []).append(line.strip())
                continue
            line = line.strip()
            if not line: continue
            parts = line.split('  - ')
            if len(parts) < 2:
                continue
            field = parts[0]
            last_field = field
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

#!/usr/bin/env python

'''this file to be called from the command line, expects RIS input on stdin.
Returns a list of record dicts, and metadata on stdout

Details of the RIS format
http://en.wikipedia.org/wiki/RIS_%28file_format%29
'''

import chardet, cStringIO
import sys
import json

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

class RISParser(object):

    def __init__(self, fileobj):

        data = fileobj.read()
        self.encoding = chardet.detect(data).get('encoding', 'ascii')

        # Some files have Byte-order marks inserted at the start
        if data[:3] == '\xef\xbb\xbf':
            data = data[3:]
        self.fileobj = cStringIO.StringIO(data)
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

def parse():
    parser = RISParser(sys.stdin)
    records, metadata = parser.parse()
    if len(records) > 0:
        sys.stdout.write(json.dumps({'records':records, 'metadata':metadata}))
    else:
        sys.stderr.write('Zero records were parsed from the data')
    
def main():
    conf = {"display_name": "RIS",
            "format": "ris",
            "contact": "openbiblio-dev@lists.okfn.org", 
            "bibserver_plugin": True, 
            "BibJSON_version": "0.81"}        
    for x in sys.argv[1:]:
        if x == '-bibserver':
            sys.stdout.write(json.dumps(conf))
            sys.exit()
    parse()
            
if __name__ == '__main__':
    main()
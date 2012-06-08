#!/usr/bin/env python
import csv
import sys
import json
import chardet
import cStringIO

class CSVParser(object):

    def __init__(self, fileobj):

        data = fileobj.read()
        self.encoding = chardet.detect(data).get('encoding', 'ascii')

        # Some files have Byte-order marks inserted at the start
        if data[:3] == '\xef\xbb\xbf':
            data = data[3:]
        self.fileobj = cStringIO.StringIO(data)


    def parse(self):
        #dialect = csv.Sniffer().sniff(fileobj.read(1024))
        d = csv.DictReader(self.fileobj)
        data = []

        # do any required conversions
        for row in d:
            if "author" in row:
                row["author"] = [{"name":i} for i in row["author"].split(",")]
            if "editor" in row:
                row["editor"] = [{"name":i} for i in row["editor"].split(",")]
            if "journal" in row:
                row["journal"] = {"name":row["journal"]}
            data.append(row)
        return data, {}
        
def parse():
    parser = CSVParser(sys.stdin)
    records, metadata = parser.parse()
    if len(records) > 0:
        sys.stdout.write(json.dumps({'records':records, 'metadata':metadata}))
    else:
        sys.stderr.write('Zero records were parsed from the data')

def main():
    conf = {"display_name": "CSV",
            "format": "csv",
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

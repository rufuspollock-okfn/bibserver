#!/usr/bin/env python

import chardet
import cStringIO
import json
import sys


class JSONParser(object):

    def __init__(self, fileobj):

        data = fileobj.read()
        self.encoding = chardet.detect(data).get('encoding', 'ascii')

        # Some files have Byte-order marks inserted at the start
        if data[:3] == '\xef\xbb\xbf':
            data = data[3:]
        self.fileobj = cStringIO.StringIO(data)

    def parse(self):
        incoming = json.load(self.fileobj)

        if 'records' in incoming:
            # if the incoming is bibjson, get records and metadata
            data = self.customisations(incoming['records'])
            metadata = incoming.get('metadata', {})
        else:
            data = incoming
            metadata = {}

        return data, metadata

    def customisations(self, records):
        for record in records:
            # tidy any errant authors as strings
            if 'author' in record:
                if ' and ' in record['author']:
                    record['author'] = record['author'].split(' and ')
            # do any conversions to objects
            for index, item in enumerate(record.get('author', [])):
                if not isinstance(item, dict):
                    record['author'][index] = {"name": item}
            # copy an citekey to cid
            if 'citekey' in record:
                record['id'] = record['citekey']
            if 'cid' in record:
                record['id'] = record['cid']
            # copy keys to singular
            if 'links' in record:
                record['link'] = record['links']
                del record['links']
        return records


def parse():
    parser = JSONParser(sys.stdin)
    records, metadata = parser.parse()
    if len(records) > 0:
        sys.stdout.write(
            json.dumps({'records': records, 'metadata': metadata})
        )
    else:
        sys.stderr.write('Zero records were parsed from the data')


def main():
    conf = {"display_name": "JSON",
            "format": "json",
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

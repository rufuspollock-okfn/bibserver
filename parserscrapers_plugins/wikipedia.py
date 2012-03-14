#!/usr/bin/env python

'''
Wikipedia search to citations parser
Reads a query term on stdin
'''

import os, sys
import re
import json
import urllib, urllib2

def wikitext_to_dict(txt):
    buf = []
    for c in re.findall('{{Citation |cite journal(.*?)}}', txt):
        if c.strip().startswith('needed'): continue
        tmp = {}
        for cc in c.split('|'):
            ccc = cc.strip().split('=')
            if len(ccc) == 2:
                tmp[ccc[0].strip()] = ccc[1].strip()
        if tmp:
            name = '%s %s' % (tmp.get('first',''), tmp.get('last', ''))
            if name.strip():
                tmp['author'] = [{'name':name}]
            if 'journal' in tmp:
                tmp['journal'] = {'name':tmp['journal']}
            buf.append(tmp)
    return buf
    
def parse():
    q = sys.stdin.read()
    URL = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit=50&srprop=wordcount&format=json&srsearch='
    URLraw = 'http://en.wikipedia.org/w/index.php?action=raw&title='
    data = urllib2.urlopen(URL+urllib.quote_plus(q)).read()
    data_json = json.loads(data)
    records = []
    for x in data_json["query"]["search"]:
        if x['wordcount'] > 20:
            quoted_title = urllib.quote_plus(x['title'].encode('utf8'))
            title_data = urllib2.urlopen(URLraw+quoted_title).read()
            citations = wikitext_to_dict(title_data)
            if citations:
                for c in citations:
                    c['link'] = [{'url':'http://en.wikipedia.org/wiki/'+quoted_title}]
                records.extend(citations)
    sys.stdout.write(json.dumps({'records':records, 'metadata':{}}))
    
def main():
    conf = {"display_name": "Wikipedia search to citations",
            "format": "wikipedia",
            "downloads": True,
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
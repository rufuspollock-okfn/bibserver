#!/usr/bin/env python

'''
Wikipedia search to citations parser
Reads a query term on stdin
'''

import os, sys
import re
import json
import urllib, urllib2, httplib
import traceback

def repl(matchobj):
    return matchobj.group(0)

def wikitext_to_dict(txt):
    buf = []
    for c in re.findall('{{Citation |cite journal(.*?)}}', txt):
        if c.strip().startswith('needed'): continue
        c = re.sub('{{.*?|.*?|(.*?)}}', repl, c)
        tmp = {}
        for cc in c.split('|'):
            ccc = cc.strip().split('=')
            if len(ccc) == 2:
                tmp[ccc[0].strip()] = ccc[1].strip()
        if tmp:
            if 'author' in tmp:
                auth_string = tmp['author'].split(',')
                tmp['author'] = []
                for au in auth_string:
                    au = au.strip()
                    if au.startswith('and '):
                        au = au[4:]
                    tmp.setdefault('author', []).append({'name':au})
            name = '%s %s' % (tmp.get('first',''), tmp.get('last', ''))
            if name.strip():
                tmp.setdefault('author', []).append({'name':name})
            if 'journal' in tmp:
                tmp['journal'] = {'name':tmp['journal']}
            buf.append(tmp)
    return buf
    
def parse(local_cache):
    q = sys.stdin.read()
    URL = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit=50&srprop=wordcount&format=json&srsearch='
    URLraw = 'http://en.wikipedia.org/w/index.php?action=raw&title='
    data_json = False
    if local_cache:
        try:
            cached_data = json.loads(open('wikipedia.py.data').read())
            data_json = cached_data.get('data1', {})
        except IOError:
            cached_data = {'data1':{}, 'data2':{}}            
    if not data_json:
        data = urllib2.urlopen(URL+urllib.quote_plus(q)).read()
        data_json = json.loads(data)
    if local_cache:
        cached_data['data1'] = data_json
    records = []
    
    try:
        search_result = data_json.get("query")
        if not search_result: search_result = data_json.get("query-continue", {"search":[]})
        for x in search_result["search"]:
            if x['wordcount'] > 20:
                quoted_title = urllib.quote_plus(x['title'].encode('utf8'))
                try:
                    title_data = None
                    if local_cache:
                        title_data = cached_data.get('data2',{}).get(quoted_title)
                    if title_data is None:
                        title_data = urllib2.urlopen(URLraw+quoted_title).read()
                    if local_cache:
                        cached_data.setdefault('data2', {})[quoted_title] = title_data
                except httplib.BadStatusLine:
                    sys.stderr.write('Problem reading %s\n' % (URLraw+quoted_title))
                    continue
                citations = wikitext_to_dict(title_data)
                if citations:
                    for c in citations:
                        c['link'] = [{'url':'http://en.wikipedia.org/wiki/'+quoted_title}]
                    records.extend(citations)
    except:
        sys.stderr.write(traceback.format_exc())
    sys.stdout.write(json.dumps({'records':records, 'metadata':{}}))
    if local_cache:
        open('wikipedia.py.data', 'w').write(json.dumps(cached_data))
    
def main():
    conf = {"display_name": "Wikipedia search to citations",
            "format": "wikipedia",
            "downloads": True,
            "contact": "openbiblio-dev@lists.okfn.org", 
            "bibserver_plugin": True, 
            "BibJSON_version": "0.81"}
    local_cache = False        
    for x in sys.argv[1:]:
        if x == '-bibserver':
            sys.stdout.write(json.dumps(conf))
            sys.exit()
        elif x == '-cache':
            local_cache = True
    parse(local_cache)
            
if __name__ == '__main__':
    main()
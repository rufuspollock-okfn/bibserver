#!/usr/bin/env python

'''
BibJSON identity parser.
Reads a valid BibJSON input on stdin, parses it as a JSON file.
Performs some basic validation, and outputs the serialised BibJSON on stdout.
'''

import os, sys
import json

def parse():
    data = sys.stdin.read()
    data_json = json.loads(data)
    sys.stdout.write(json.dumps(data_json, indent=2))
    
def main():
    conf = {"display_name": "BibJSON Identity Parser",
            "format": "jsoncheck",
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
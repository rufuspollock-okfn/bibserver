'''
Independent running process.
Handling uploads asynchronously.
See: https://github.com/okfn/bibserver/wiki/AsyncUploadDesign
'''

import os, stat, sys
import subprocess
import requests
import hashlib
import json
from datetime import datetime
import traceback
import bibserver.dao
from bibserver.config import config

def parse(ticket):
    ticket['state'] = 'parsing'
    ticket.save()
    if 'data_md5' not in ticket:
        ticket.fail('Attempt to parse ticket, but no data_md5 found')
        return
    p = PLUGINS.get(ticket['format'])
    if not p:
        ticket.fail('Parser plugin for format %s not found' % ticket['format'])
    # Make sure the downloaded content is in the cache
    download_cache_directory = config['download_cache_directory']
    in_path = os.path.join(download_cache_directory, ticket['data_md5'])
    if not os.path.exists(in_path):
        ticket.fail('Downloaded content for %s not found' % in_path)
        return        
    json_data = subprocess.check_output(p['_path'], shell=True, stdin=open(in_path))
    bibjson_cache_directory = config['bibjson_cache_directory']
    out_path = os.path.join(bibjson_cache_directory, ticket['data_md5']) + '.bibjson'
    open(out_path, 'wb').write(json_data)
    ticket['state'] = 'parsed'
    ticket.save()
    

def download(ticket):
    ticket['state'] = 'downloading'
    ticket.save()
    r = requests.get(ticket['source_url'])
    r.raise_for_status()
    md5sum = hashlib.md5(r.content).hexdigest()
    download_cache_directory = config['download_cache_directory']
    out_path = os.path.join(download_cache_directory, md5sum)
    if not os.path.exists(out_path):
        open(out_path, 'wb').write(r.content)
    ticket['data_md5'] = md5sum
    ticket['state'] = 'downloaded'
    ticket.save()
    
    
def determine_action(ticket):
    'For the given ticket determine what the next action to take is based on the state'
    state = ticket['state']
    if state == 'new':
        download(ticket)
    if state == 'downloaded':
        parse(ticket)

def get_tickets(state=None):
    "Get tickets with the given state"
    if state:
        q = bibserver.dao.IngestTicket.query(terms={'state':state})
    else:
        q = bibserver.dao.IngestTicket.query()
    return [bibserver.dao.IngestTicket(**x) for x in q['hits']['hits']]
    
def scan_parserscrapers(directory):
    "Scan the specified directory for valid parser/scraper executables"
    found = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            filename = os.path.join(root, name)
            is_ex = stat.S_IXUSR & os.stat(filename)[stat.ST_MODE]            
            if is_ex:
                # Try and call this executable with a -v to get a config
                try:
                    output = subprocess.check_output(filename+' -v', shell=True)
                    output_json = json.loads(output)
                    if output_json['bibserver_plugin']:
                        output_json['_path'] = filename
                        found.append(output_json)
                except subprocess.CalledProcessError:
                    pass
                except ValueError:
                    sys.stderr.write('Error parsing plugin output:\n')
                    sys.stderr.write(output)
                    pass
    return found
    
def init():
    for d in ('download_cache_directory', 'parserscrapers_plugin_directory', 'bibjson_cache_directory'):
        dd = config.get(d)
        if not os.path.exists(dd):
            os.mkdir(dd)

def run():

    parserscrapers_plugin_directory = config.get('parserscrapers_plugin_directory')
    if not parserscrapers_plugin_directory:
        sys.stderr.write('Error: parserscrapers_plugin_directory config entry not found\n')
        sys.exit(2)
    plugins = scan_parserscrapers(parserscrapers_plugin_directory)
    if plugins:
        for ps in plugins:
            PLUGINS[ps['format']] = ps
        print 'Plugins found:', ', '.join(PLUGINS.keys())
    
    for state in ('new', 'downloaded'):
        for t in get_tickets(state):
            try:
                determine_action(t)
            except:
                exc = traceback.format_exc()
                err = (datetime.now().isoformat(), exc)
                t.fail(err)
                sys.stderr.write(exc)

def reset_all_tickets():
    for t in get_tickets():
        t['state'] = 'new'
        t.save()
        
if __name__ == '__main__':
    PLUGINS = {}
    init()
    for x in sys.argv[1:]:
        if x == '-x':
            reset_all_tickets()
        if x == '-p':
            for t in get_tickets():
                print t
    if len(sys.argv) == 1:
        run()
    
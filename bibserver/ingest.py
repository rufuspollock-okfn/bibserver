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
from bibserver.importer import Importer
from bibserver.core import app
from flask import render_template, make_response, abort, send_from_directory

# Constant used to track installed plugins
PLUGINS = {}

def index(ticket):
    ticket['state'] = 'populating_index'
    ticket.save()
    # Make sure the parsed content is in the cache
    download_cache_directory = config['download_cache_directory']
    in_path = os.path.join(download_cache_directory, ticket['data_md5']) + '.bibjson'
    if not os.path.exists(in_path):
        ticket.fail('Parsed content for %s not found' % in_path)
        return
    record_dicts = json.loads(open(in_path).read())
    # TODO check for metadata section to update collection from this?
    owner = bibserver.dao.Account.get(ticket['owner'])
    importer = Importer(owner=owner)
    collection = {
        'label': ticket['collection'],
        'description': ticket.get('description'),
        'source': ticket['source_url'],
        'format': ticket['format']
    }
    importer.index(collection, record_dicts)
    ticket['state'] = 'done'
    ticket.save()
    
def parse(ticket):
    ticket['state'] = 'parsing'
    ticket.save()
    if 'data_md5' not in ticket:
        ticket.fail('Attempt to parse ticket, but no data_md5 found')
        return
    p = PLUGINS.get(ticket['format'])
    if not p:
        ticket.fail('Parser plugin for format %s not found' % ticket['format'])
        return
    # Make sure the downloaded content is in the cache
    download_cache_directory = config['download_cache_directory']
    in_path = os.path.join(download_cache_directory, ticket['data_md5'])
    if not os.path.exists(in_path):
        ticket.fail('Downloaded content for %s not found' % in_path)
        return
    json_data = subprocess.check_output(p['_path'], shell=True, stdin=open(in_path))
    download_cache_directory = config['download_cache_directory']
    out_path = os.path.join(download_cache_directory, ticket['data_md5']) + '.bibjson'
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
    try:
        state = ticket['state']
        print 'Trying:', ticket['id'], ticket['state'],
        if state == 'new':
            download(ticket)
        if state == 'downloaded':
            parse(ticket)
        if state == 'parsed':
            index(ticket)
    except:
        ## TODO
        # For some reason saving the traceback to the ticket here is not saving the exception
        # The ticket does not record the 'failed' state, and remains in eg. a 'downloading' state
        exc = traceback.format_exc()
        err = (datetime.now().isoformat(), exc)
        ticket.fail(err)
    print '...', ticket['state']

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
                    sys.stderr.write(traceback.format_exc())
                except ValueError:
                    sys.stderr.write('Error parsing plugin output:\n')
                    sys.stderr.write(output)
    return found
    
def init():
    for d in ('download_cache_directory', 'parserscrapers_plugin_directory'):
        dd = config.get(d)
        if not os.path.exists(dd):
            os.mkdir(dd)

    # Scan for available parser/scraper plugins
    parserscrapers_plugin_directory = config.get('parserscrapers_plugin_directory')
    if not parserscrapers_plugin_directory:
        sys.stderr.write('Error: parserscrapers_plugin_directory config entry not found\n')
        sys.exit(2)
    plugins = scan_parserscrapers(parserscrapers_plugin_directory)
    if plugins:
        for ps in plugins:
            PLUGINS[ps['format']] = ps
        print 'Plugins found:', ', '.join(PLUGINS.keys())

def run():
    for state in ('new', 'downloaded', 'parsed'):
        for t in get_tickets(state):
            determine_action(t)

def reset_all_tickets():
    for t in get_tickets():
        print 'Resetting', t['id']
        t['state'] = 'new'
        t.save()

@app.route('/ticket/')
@app.route('/ticket/<ticket_id>')
def view_ticket(ticket_id=None):
    ingest_tickets = get_tickets()
    if ticket_id:
        t = bibserver.dao.IngestTicket.get(ticket_id)
    elif ingest_tickets:
        t = ingest_tickets[0]
    else:
        t = None
    return render_template('tickets/view.html', ticket=t, ingest_tickets = ingest_tickets)

@app.route('/ingest/<md5sum>')
def serve(md5sum):
    path = config['download_cache_directory']
    if not path.startswith('/'):
        path = os.path.join(os.getcwd(), path)
    
    return send_from_directory(path, md5sum)
    
if __name__ == '__main__':
    init()
    for x in sys.argv[1:]:
        if x == '-x':
            reset_all_tickets()
        if x == '-p':
            for t in get_tickets():
                print t
    if len(sys.argv) == 1:
        run()
    
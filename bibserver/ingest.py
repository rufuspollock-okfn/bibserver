'''
Independent running process.
Handling uploads asynchronously.
See: https://github.com/okfn/bibserver/wiki/AsyncUploadDesign
'''

import os, stat, sys, uuid, time
import subprocess
from cStringIO import StringIO
import requests
import hashlib
import json
from datetime import datetime
import traceback
import bibserver.dao
from bibserver.config import config
from bibserver.importer import Importer
from bibserver.core import app
import bibserver.util as util
from flask import render_template, make_response, abort, send_from_directory, redirect, request

# Constant used to track installed plugins
PLUGINS = {}

class IngestTicketInvalidOwnerException(Exception):
    pass
class IngestTicketInvalidInit(Exception):
    pass
class IngestTicketInvalidId(Exception):
    pass
    
class IngestTicket(dict):
    def __init__(self,*args,**kwargs):        
        'Creates a new Ingest Ticket, ready for processing by the ingest pipeline'
        if '_id' not in kwargs:
            kwargs['_id'] = uuid.uuid4().hex
        if 'state' not in kwargs:
            kwargs['state'] = 'new'
        if '_created' not in kwargs:
            kwargs['_created'] = time.time()
        owner = kwargs.get('owner')
        if not type(owner) in (str, unicode):
            raise IngestTicketInvalidOwnerException()
        for x in ('collection', 'format'):
            if not kwargs.get(x):
                raise IngestTicketInvalidInit('You need to supply the parameter %s' % x)
        for x in ('_created', '_last_modified'):
            if x in kwargs:
                kwargs[x] = datetime.fromtimestamp(kwargs[x])
        dict.__init__(self,*args,**kwargs)
    
    @classmethod
    def load(cls, ticket_id):
        filename = os.path.join(config['download_cache_directory'], ticket_id)  + '.ticket'
        if not os.path.exists(filename):
            raise IngestTicketInvalidId(ticket_id)
        data = json.loads(open(filename).read())
        return cls(**data)
        
    def save(self):
        self['_last_modified'] = time.time()
        self['_created'] = time.mktime(self['_created'].timetuple())
        filename = os.path.join(config['download_cache_directory'], self['_id'])  + '.ticket'
        open(filename, 'wb').write(json.dumps(self))
        for x in ('_created', '_last_modified'):
            self[x] = datetime.fromtimestamp(self[x])
        
    def fail(self, msg):
        self['state'] = 'failed'
        err = (datetime.now().strftime("%Y%m%d%H%M"), msg)
        self.setdefault('exception', []).append(err)
        self.save()

    def delete(self):
        filename = os.path.join(config['download_cache_directory'], self['_id'])  + '.ticket'
        os.remove(filename)
        
    def __unicode__(self):
        try:
            return u'%s/%s,%s [%s] - %s' % (self['owner'], self['collection'], self['format'], self['state'], self['_last_modified'])
        except:
            return repr(self)
        
    def __str__(self):
        return unicode(self).encode('utf8')
        
    @property
    def id(self):
        return self['_id']

def index(ticket):
    ticket['state'] = 'populating_index'
    ticket.save()
    # Make sure the parsed content is in the cache
    download_cache_directory = config['download_cache_directory']
    in_path = os.path.join(download_cache_directory, ticket['data_json'])
    if not os.path.exists(in_path):
        ticket.fail('Parsed content for %s not found' % in_path)
        return
    data = open(in_path).read()
    if len(data) < 1:
        raise Exception('The parsed data in this ticket is empty.' )
    
    # TODO check for metadata section to update collection from this?
    owner = bibserver.dao.Account.get(ticket['owner'])
    importer = Importer(owner=owner)
    collection = {
        'label': ticket['collection'],
        'collection': util.slugify(ticket['collection']),
        'description': ticket.get('description'),
        'source': ticket['source_url'],
        'format': ticket['format'],
        'license': ticket.get('license', u"Not specified"),
    }
    collection, records = importer.upload(open(in_path), collection)
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
    p = subprocess.Popen(p['_path'], shell=True, stdin=open(in_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE)    
    data = p.stdout.read()
    md5sum = hashlib.md5(data).hexdigest()
    download_cache_directory = config['download_cache_directory']    
    out_path = os.path.join(download_cache_directory, md5sum)
    open(out_path, 'wb').write(data)
    
    ticket['data_json'] = md5sum
    if ticket.get('only_parse') == True:
        ticket['state'] = 'done'
    else:
        ticket['state'] = 'parsed'
    # Check if there is any data in the stderr of the parser
    # If so, add it to the ticket as potential feedback
    data_stderr = p.stderr.read()
    if len(data_stderr) > 0:
        ticket['parse_feedback'] = data_stderr
    ticket.save()
    
def store_data_in_cache(data):
    md5sum = hashlib.md5(data).hexdigest()
    download_cache_directory = config['download_cache_directory']
    out_path = os.path.join(download_cache_directory, md5sum)
    if not os.path.exists(out_path):
        open(out_path, 'wb').write(data)
    return md5sum
    
def download(ticket):
    ticket['state'] = 'downloading'
    ticket.save()
    p = PLUGINS.get(ticket['format'])
    if p and p.get('downloads'):
        data = ticket['source_url'].strip()
        content_type = 'text/plain'
    else:
        url = ticket['source_url'].strip()
        r = requests.get(url)
        content_type = r.headers['content-type']
        r.raise_for_status()
        data = r.content
        if len(data) < 1:
            ticket.fail('Data is empty, HTTP status code %s ' % r.status_code)
            return
        
    ticket['data_md5'] = store_data_in_cache(data)
    ticket['data_content_type'] = content_type

    ticket['state'] = 'downloaded'
    ticket.save()
    
    
def determine_action(ticket):
    'For the given ticket determine what the next action to take is based on the state'
    try:
        state = ticket['state']
        print ticket['state'], ticket['_id'],
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
        ticket.fail(traceback.format_exc())
    print '...', ticket['state']

def get_tickets(state=None):
    "Get tickets with the given state"
    buf = []
    for f in os.listdir(config['download_cache_directory']):
        if f.endswith('.ticket'):
            t = IngestTicket.load(f[:-7])
            if not state or (state == t['state']):
                buf.append(t)
    return buf
    
def scan_parserscrapers(directory):
    "Scan the specified directory for valid parser/scraper executables"
    found = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            filename = os.path.join(root, name)
            is_ex = stat.S_IXUSR & os.stat(filename)[stat.ST_MODE]            
            if is_ex:
                # Try and call this executable with a -bibserver to get a config
                try:
                    output = subprocess.check_output(filename+' -bibserver', shell=True)
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

def get_plugins():
    filename = os.path.join(config.get('parserscrapers_plugin_directory'), 'plugins.json')
    return json.loads(open(filename).read())
    
def init():
    for d in ('download_cache_directory', 'parserscrapers_plugin_directory'):
        dd = config.get(d)
        if not os.path.exists(dd):
            os.mkdir(dd)

    # Scan for available parser/scraper plugins
    parserscrapers_plugin_directory = config.get('parserscrapers_plugin_directory')
    if not parserscrapers_plugin_directory:
        sys.stderr.write('Error: parserscrapers_plugin_directory config entry not found\n')
    plugins = scan_parserscrapers(parserscrapers_plugin_directory)
    if plugins:
        for ps in plugins:
            PLUGINS[ps['format']] = ps
    filename = os.path.join(config.get('parserscrapers_plugin_directory'), 'plugins.json')
    open(filename, 'w').write(json.dumps(PLUGINS))

def run():
    last_flash = time.time() - 500
    count = 0
    running = True
    while running:
        try:
            pid = open('ingest.pid').read()
            if str(pid) != str(os.getpid()):
                print 'Other ingest process %s detected not %s, exiting' % (pid, os.getpid())
                sys.exit(2)
        except IOError:
            print 'Ingest process exiting: ingest.pid file cound not be read'
            sys.exit(3)
        except:
            traceback.print_exc()
            sys.exit(4)
        for state in ('new', 'downloaded', 'parsed'):
            for t in get_tickets(state):
                determine_action(t)
                count += 1
        time.sleep(15)
        if time.time() - last_flash > (5 * 60):
            sys.stdout.write('Ingest pipeline %s %s performed %s actions\n' % (os.getpid(), time.ctime(), count))
            last_flash = time.time()

def reset_all_tickets():
    for t in get_tickets():
        print 'Resetting', t['_id']
        t['state'] = 'new'
        t.save()

@app.route('/ticket/')
@app.route('/ticket/<ticket_id>')
def view_ticket(ticket_id=None):
    ingest_tickets = get_tickets()
    sort_key = request.values.get('sort')
    if sort_key:
        ingest_tickets.sort(key=lambda x: x.get(sort_key))
    if ticket_id:
        try:
            t = IngestTicket.load(ticket_id)
        except bibserver.ingest.IngestTicketInvalidId:
            abort(404)
    else:
        t = None
    return render_template('tickets/view.html', ticket=t, ingest_tickets = ingest_tickets)

@app.route('/ticket/<ticket_id>/<payload>', methods=['GET', 'POST'])
def ticket_serve(ticket_id, payload):
    t = IngestTicket.load(ticket_id)
    if payload == 'data':
        filename = t['data_md5']
    elif payload == 'bibjson':
        filename = t['data_json']
    elif (payload == 'reset') and (request.method == 'POST'):
        t['state'] =  'new'
        for cleanfield in ('failed_index', 'parse_feedback'):
            if cleanfield in t:
                del t[cleanfield]
        t.save()
        return make_response('OK')
    elif (payload == 'delete') and (request.method == 'POST'):
        t.delete()
        return make_response('OK')
    return redirect('/data/'+filename)

@app.route('/data.txt')
def data_list():
    'Output a list of all the raw data files, one file per line'
    data_list = []
    for t in get_tickets():
        if 'data_json' in t:
            data_list.append('/data/' + t['data_json'])
    resp = make_response( '\n'.join(data_list) )
    resp.mimetype = "text/plain"
    return resp

@app.route('/data/<filename>')
def data_serve(filename):
    path = config['download_cache_directory']
    if not path.startswith('/'):
        path = os.path.join(os.getcwd(), path)
    response = send_from_directory(path, filename)
    response.headers['Content-Type'] = 'text/plain'
    return response
    
if __name__ == '__main__':
    init()
    for x in sys.argv[1:]:        
        if x == '-x':
            reset_all_tickets()
        elif x.startswith('-p'):
            for t in get_tickets():
                print t
                if x == '-pp':
                    print '-' * 80
                    for k,v in t.items():
                        print ' '*4, k+':', v
        elif x == '-d':
            open('ingest.pid', 'w').write('%s' % os.getpid())
            run()
    if len(sys.argv) == 1:
        run()
    

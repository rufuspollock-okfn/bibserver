'''this file can be called as a module or called directly from the command line like so:

python RISParser.py /path/to/file.txt
Returns a list of record dicts

Details of the RIS format
http://en.wikipedia.org/wiki/RIS_%28file_format%29
'''

class BibTexParser(object):
    def parse(self, fileobj):
        data, chunk = [], {}
        for line in fileobj.readlines():
            line = line.strip()
            if not line: continue
            parts = line.split('  - ')
            if len(parts) < 2: continue
            field = parts[0]
            if field == 'TY':
                if chunk: data.append(chunk)
                chunk = {}
            value = '  - '.join(parts[1:])
            if value:
                chunk.setdefault(field, []).append(value)
        if chunk: data.append(chunk)
        return data, {}
        
# in case file is run directly
if __name__ == "__main__":
    import sys, json
    parser = BibTexParser()
    fileobj = open(sys.argv[1])
    data = parser.parse(fileobj)
    sys.stdout.write(json.dumps(data, indent=2))

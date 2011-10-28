# convert a source file to bibjson

from parsers.BibTexParser import BibTexParser
from parsers.JSONParser import JSONParser
from parsers.BibJSONParser import BibJSONParser
from parsers.JSONLDParser import JSONLDParser
from parsers.CSVParser import CSVParser

class Parser(object):
    
    def parse(self, fileobj, format):
        '''Convert a source datastream in fileobj in `format` (e.g. bibtex) to
        bibjson and add it to `collection`.

        :return: a python dict json-i-fiable to bibjson.
        '''
        if format == "bibtex" or format == "bib":
            parser = BibTexParser()
            data, metadata = parser.parse(fileobj)
        elif format == "json":
            parser = JSONParser()
            data, metadata = parser.parse(fileobj)        
        elif format == "bibjson":
            parser = BibJSONParser()
            data, metadata = parser.parse(fileobj)
        elif format == "json-ld":
            parser = JSONLDParser()
            data, metadata = parser.parse(fileobj)
        elif format == "csv" or format == "google":
            parser = CSVParser()
            data, metadata = parser.parse(fileobj)
        else:
            raise Exception('Unable to convert from format: %s' % format)

        return data, metadata
    
    









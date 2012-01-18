# convert a source file to bibjson

from parsers.BibTexParser import BibTexParser
from parsers.JSONParser import JSONParser
from parsers.CSVParser import CSVParser
from parsers.RISParser import RISParser

class Parser(object):
    
    def parse(self, fileobj, format):
        '''Convert a source datastream in fileobj in `format` (e.g. bibtex) to
        bibjson and add it to `collection`.

        :return: a python dict json-i-fiable to bibjson.
        '''
        if format == "bibtex" or format == "bib":
            parser = BibTexParser(fileobj)
        elif format == "json":
            parser = JSONParser(fileobj)
        elif format == "csv" or format == "google":
            parser = CSVParser(fileobj)
        elif format == "ris":
            parser = RISParser(fileobj)
        else:
            raise Exception('Unable to convert from format: %s' % format)
        data, metadata = parser.parse()
        return data, metadata
    
    









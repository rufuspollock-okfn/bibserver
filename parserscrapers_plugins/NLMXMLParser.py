from xml.etree.ElementTree import ElementTree
from bibserver.parsers import BaseParser

'''this file can be called as a module or called directly from the command line like so:

python NLMXMLParser.py /path/to/file.xml

Returns a list of record dicts
Or just parse a record directly like so:

python NLMXMLParser.py '<?xml version='1.0'?><art>...'

Returns a record dict
'''



class NLMXMLParser(BaseParser):

    def __init__(self, fileobj):
        super(NLMXMLParser, self).__init__(fileobj)

        # set which bibjson schema this parser parses to
        self.schema = "v0.82"
        self.has_metadata = False
        self.persons = []

        self.identifier_types = ["doi","isbn","issn"]


    def parse(self):
        '''given a fileobject, parse it for NLM XML records,
        and pass them to the record parser'''
        records = []

        et = ElementTree()
        et.parse(self.fileobj)

        records.append(self.parse_front_matter(et.find('front')))

        records.extend(self.parse_references(et.findall('back/ref-list/ref')))

        return records, {"schema": self.schema}


    def parse_front_matter(self, front):

        article_meta = front.find('article-meta')
        journal_meta = front.find('journal-meta')

        record = {
            'title': self.get_article_title(article_meta),
            'author': self.get_article_authors(article_meta),
            'year': article_meta.findtext('pub-date/year'),
            'volume': article_meta.findtext('volume'),
            'number': article_meta.findtext('issue'),
            'pages': self.get_page_numbers(article_meta),

            'journal': self.get_journal_name(journal_meta),
            'publisher': self.get_journal_publisher_name(journal_meta)
        }

        doi = front.findtext('article-meta/article-id[@pub-id-type="doi"]')
        record['identifiers'] = [
            {'id': doi, 'type': 'doi'}
        ]

        return record

    def parse_references(self, ref_list):
        records = []
        for ref in ref_list:
            records.append(self.parse_reference(ref))
        return records

    def parse_reference(self, reference):

        citation = reference.find('citation')

        if citation.attrib['citation-type'] == 'journal':
            record = self.parse_journal(citation)

        elif citation.attrib['citation-type'] == 'other':
            record = self.parse_other(citation)

        else:
            raise Exception('Unsupported citation type: ' + citation.attrib['citation-type'])

        record['citekey'] = reference.attrib['id']

        return record

    def parse_journal(self, citation):
        return self.filter_empty_fields({
                'title': self.get_journal_citation_title(citation),
                'author': self.get_citation_authors(citation),
                'year': citation.findtext('year'),
                'journal': citation.findtext('source'),
                'volume': citation.findtext('volume'),
                'pages': self.get_page_numbers(citation)
            })

    def parse_other(self, citation):
        return self.filter_empty_fields({
                'title': self.get_other_citation_title(citation),
                'booktitle': self.get_other_citation_booktitle(citation),
                'author': self.get_citation_authors(citation),
                'editor': self.get_citation_editors(citation),
                'year': citation.findtext('year'),
                'publisher': self.get_citation_publisher(citation),
                'volume': citation.findtext('volume'),
                'pages': self.get_page_numbers(citation)
            })


    def get_article_title(self, article_meta):
        return "".join(article_meta.find('title-group/article-title').itertext())

    def get_article_authors(self, article_meta):
        return self.get_names(article_meta.findall('contrib-group/contrib[@contrib-type="author"]/name'))

    def get_page_numbers(self, context):
        if context.find('fpage') is None:
            return context.findtext('elocation-id')
        elif context.find('lpage') is None:
            return context.findtext('fpage')
        else:
            return '%s--%s' % (context.findtext('fpage'), context.findtext('lpage'))

    def get_journal_citation_title(self, citation):
        if citation.find('article-title') is None:
            return None
        else:
            return "".join(citation.find('article-title').itertext())

    def get_other_citation_title(self, citation):
        if citation.find('article-title') is None:
            return self.get_citation_source(citation)
        else:
            return "".join(citation.find('article-title').itertext())

    def get_other_citation_booktitle(self, citation):
        if citation.find('article-title') is None:
            return None
        else:
            return self.get_citation_source(citation)

    def get_citation_source(self, citation):
        if citation.find('source') is None:
            return None
        else:
            return "".join(citation.find('source').itertext())

    def get_citation_publisher(self, context):
        if context.find('publisher-name') is None:
            return None
        elif context.find('publisher-loc') is None:
            return context.findtext('publisher-name')
        else:
            return context.findtext('publisher-name') + ', ' + context.findtext('publisher-loc')


    def get_citation_authors(self, citation):
        return self.get_names(citation.findall('person-group[@person-group-type="author"]/name'))

    def get_citation_editors(self, citation):
        return self.get_names(citation.findall('person-group[@person-group-type="editor"]/name'))

    def get_journal_name(self, journal_meta):
        return journal_meta.findtext('.//journal-title');

    def get_journal_publisher_name(self, journal_meta):
        return journal_meta.findtext('.//publisher-name');


    def get_names(self, names):
        return ['%s, %s' % (name.findtext('surname'), name.findtext('given-names')) for name in names]

    def filter_empty_fields(self, dict):
        record = {}
        for k, v in dict.iteritems():
            if not v is None:
                record[k] = v
        return record


# in case file is run directly
if __name__ == "__main__":
    import sys
    parser = NLMXMLParser(open(sys.argv[1]))
    print parser.parse()




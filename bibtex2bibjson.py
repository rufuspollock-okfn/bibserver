import json

bibtex_vocab = {
    "address" : ("http://swrc.ontoware.org/ontology#", "address"), # Publisher's address (usually just the city, but can be the full address for lesser-known publishers)
    "annote" : None, # An annotation for annotated bibliography styles (not typical)
    "author" : ("http://swrc.ontoware.org/ontology#", "author"), #author: The name(s) of the author(s) (in the case of more than one author, separated by and)
    "booktitle" : ("http://swrc.ontoware.org/ontology#", "booktitle"), # The title of the book, if only part of it is being cited
    "chapter" : ("http://swrc.ontoware.org/ontology#", "chapter"), # The chapter number
    "crossref" : None, #The key of the cross-referenced entry
    "edition" : ("http://swrc.ontoware.org/ontology#", "edition"), # The edition of a book, long form (such as "first" or "second")
    "editor" : ("http://swrc.ontoware.org/ontology#", "editor"), #The name(s) of the editor(s)
    "eprint" : None, # A specification of an electronic publication, often a preprint or a technical report
    "howpublished" : ("http://swrc.ontoware.org/ontology#", "howpublished"), #How it was published, if the publishing method is nonstandard
    "institution" : ("http://swrc.ontoware.org/ontology#", "institution"), #The institution that was involved in the publishing, but not necessarily the publisher
    "journal" : ("http://swrc.ontoware.org/ontology#", "journal"), #The journal or magazine the work was published in
    "key" : None, #A hidden field used for specifying or overriding the alphabetical order of entries (when the "author" and "editor" fields are missing). Note that this is very different from the key (mentioned just after this list) that is used to cite or cross-reference the entry.
    "month" : ("http://swrc.ontoware.org/ontology#", "month"), #The month of publication (or, if unpublished, the month of creation)
    "note" : ("http://swrc.ontoware.org/ontology#", "note"), #Miscellaneous extra information
    "number" : ("http://swrc.ontoware.org/ontology#", "number"), # The "(issue) number" of a journal, magazine, or tech-report, if applicable. (Most publications have a "volume", but no "number" field.)
    "organization" : ("http://swrc.ontoware.org/ontology#", "organisation"), #The conference sponsor
    "pages" : ("http://swrc.ontoware.org/ontology#", "pages"), #Page numbers, separated either by commas or double-hyphens.
    "publisher" : ("http://swrc.ontoware.org/ontology#", "publisher"), #The publisher's name
    "school" : ("http://swrc.ontoware.org/ontology#", "school"), # The school where the thesis was written
    "series" : ("http://swrc.ontoware.org/ontology#", "series"), #The series of books the book was published in (e.g. "The Hardy Boys" or "Lecture Notes in Computer Science")
    "title" : ("http://swrc.ontoware.org/ontology#", "title"), #The title of the work
    "type" : ("http://swrc.ontoware.org/ontology#", "type"), #The type of tech-report, for example, "Research Note"
    "url" : None, #The WWW address
    "volume" : ("http://swrc.ontoware.org/ontology#", "volume"), #The volume of a journal or multi-volume book
    "year": ("http://swrc.ontoware.org/ontology#", "year"), #The year of publication (or, if unpublished, the year of creation)

    "article" : ("http://swrc.ontoware.org/ontology#", "Article"), #An article from a journal or magazine.
    "book" : ("http://swrc.ontoware.org/ontology#", "Book"), #A book with an explicit publisher.
    "booklet" : ("http://swrc.ontoware.org/ontology#", "Booklet"), #A work that is printed and bound, but without a named publisher or sponsoring institution.
    "conference" : ("http://swrc.ontoware.org/ontology#", "Conference"), # The same as inproceedings, included for Scribe compatibility.
    "inbook" : ("http://swrc.ontoware.org/ontology#", "InBook"), #A part of a book, usually untitled. May be a chapter (or section or whatever) and/or a range of pages.
    "incollection" : ("http://swrc.ontoware.org/ontology#", "InCollection"), #A part of a book having its own title.
    "inproceedings" : ("http://swrc.ontoware.org/ontology#", "InProceedings"), #An article in a conference proceedings.
    "manual" : ("http://swrc.ontoware.org/ontology#", "Manual"), # Technical documentation.
    "mastersthesis" : ("http://swrc.ontoware.org/ontology#", "MasterThesis"), #A Master's thesis.
    "misc" : ("http://swrc.ontoware.org/ontology#", "Misc"), #For use when nothing else fits.
    "phdthesis" : ("http://swrc.ontoware.org/ontology#", "PhDThesis"), #A Ph.D. thesis.
    "proceedings" :  ("http://swrc.ontoware.org/ontology#", "Proceedings"), #The proceedings of a conference.
    "techreport" : ("http://swrc.ontoware.org/ontology#", "TechnicalReport"), #A report published by a school or other institution, usually numbered within a series.
    "unpublished" : ("http://swrc.ontoware.org/ontology#", "Unpublished"), #A document having an author and title, but not formally published.
}

bibjson_vocab = {
    "dataset" : ("http://bibserver.berkeley.edu/terms#", "Dataset")
}

prefixes = {
    "http://swrc.ontoware.org/ontology#" : "swrc",
    "http://bibserver.berkeley.edu/terms#" : "bibjson"
}

class BibTex2BibJSON(object):

    def list_to_bibjson(self, btlist, uri, linked_dataset=False, linked_record=True):
        # self.write = lambda u: stream.write(u.encode(self.encoding, 'replace'))
        self.jsonObj = {}
        self.coerced_types = {}
        self.jsonObj["@"] = []
        
        self.add_namespaces()

        dataset = {}
        dataset["@"] = uri
        dataset["a"] = "".join(bibjson_vocab.get("dataset"))

        if linked_dataset:
            dataset["bibjson:hasRecord"] = []

        for btrecord in btlist:
            bibtype = btrecord.get('BIBTYPE')
            if bibtype == "COMMENT":
                continue
            obj = {}
            citekey = btrecord.get('CITEKEY')
            obj["@"] = "_:" + citekey
            isa = bibtex_vocab.get(bibtype.lower())
            if isa is not None:
                obj["a"] = "".join(isa)
            if linked_dataset:
                dataset["bibjson:hasRecord"].append("_:" + citekey)
            for key in btrecord:
                if key == "CITEKEY" or key == "BIBTYPE" or key == "BIBTEX":
                    continue
                maps = bibtex_vocab.get(key.lower(), (None, key.lower()))
                pred_scheme, pred_term = None, None
                if maps is None:
                    pred_scheme, pred_term = None, key.lower()
                else:
                    (pred_scheme, pred_term) = maps
                if pred_scheme is not None:
                    pred_prefix = prefixes.get(pred_scheme)
                    pred_term = pred_prefix + ":" + pred_term
                obj[pred_term] = btrecord[key]
            if linked_record:
                obj["bibjson:inDataset"] = uri
            self.jsonObj["@"].append(obj)

        self.jsonObj["@"].append(dataset)
        srlzd = json.dumps(self.jsonObj, indent=2)
        # self.write(srlzd)
        return srlzd

    def add_namespaces(self):
        namespaces = {}

        for uri in prefixes:
            namespaces[prefixes[uri]] = uri

        # add the vocab
        namespaces["#vocab"] = "http://bibserver.berkeley.edu/terms#"

        # add the namespaces to the jsonObj
        self.jsonObj["#"] = namespaces

if __name__ == "__main__":
    from parsers.BibTexParser import BibTexParser
    f = open("test/bibserver.bib")
    instring = f.read()
    f.close()
    btp = BibTexParser()
    blist = btp.parse(instring)
    b2j = BibTex2BibJSON()
    j = b2j.list_to_bibjson(blist, "http://localhost/")
    f = open("test/bib.json", "w")
    f.write(j)
    f.close()

SECRET_KEY = 'default-key'

# service and super user accounts
SERVICE_NAME = "BibSoup"
SITE_URL = "http://bibsoup.net"
EMAIL_FROM = "nobody@bibsoup.net"
HOST = "0.0.0.0"
DEBUG = True
PORT = 5000
SUPER_USER = ["test"]

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://127.0.0.1:9200"
ELASTIC_SEARCH_DB = "bibserver"

# bibserver functionality settings
# set to false if no frontend upload wanted
ALLOW_UPLOAD = True

# external API service settings and keys (should overwrite from local_config)
EXTERNAL_APIS = {
	"servicecore" : {
		"url" : "http://core.kmi.open.ac.uk/api/search/",
		"key" : "",
		"docs" : "http://core-project.kmi.open.ac.uk/api-doc/"
	}
}

# default facetview settings
FACETVIEW = {
    "search_url": "/query?",
    "datatype": "json",
    "search_index": 'elasticsearch',
    "paging":{
        "from":0,
        "size":10
    },
    "facets": []
}

# The default fields and settings for which faceting should be made available on
# for when viewing within a particular collection
INCOLL_SEARCH_FACET_FIELDS = [
    {
        "field":"collection.exact",
        "order":"term",
        "size":200,
        "display":"collection"
    },
    {
        "field":"type.exact",
        "order":"count",
        "display":"type"
    },
    {
        "field":"journal.name.exact",
        "display":"journal"
    },
    {
        "field":"author.name.exact",
        "order":"term",
        "size":500,
        "display":"author"
    },
    {
        "field":"year.exact",
        "size":100,
        "order":"reverse_term",
        "display":"year"
    }
]

# The default fields and settings for which faceting should be made available on
# for when viewing from the search everything area - if the number of records is 
# very large, facets should not be displayed on very large unique fields or it will crash
# so this should be set to an empty list
# otherwise this could be set as equal to the INCOLL facet fields above
ALL_SEARCH_FACET_FIELDS = []

# search result display layout
# a list of lists. each list represents a line on the display.
# in each line, there are objects for each key to include on the line.
# must specify the key, and optional "pre" and "post" params for displaying round it
SEARCH_RESULT_DISPLAY = [
    [
        {
            "field": "author.name"
        },
        {
            "pre": "(",
            "field": "year",
            "post": ")"
        }
    ],
    [
        {
            "pre":"<span style=\"font-weight:bold;font-size:120%;\"><a title=\"view record\" style=\"color:#666;text-decoration:underline;\" href=\"/record/",
            "field":"_id",
            "post":"\">"
        },
        {
            "field":"title",
            "post":"</a></span>"
        }
    ],
    [
        {
            "field": "howpublished"
        },
        {
            "pre": "in <em>",
            "field": "journal.name",
            "post": "</em>,"
        },
        {
            "pre": "<em>",
            "field": "booktitle",
            "post": "</em>,"
        },
        {
            "pre": "vol. ",
            "field": "volume"
        },
        {
            "field": "publisher"
        }
    ],
    [
        {
            "field": "link.url"
        }
    ]
]

# default view for collections page
COLLECTIONS_RESULT_DISPLAY = [
    [
        {
            "pre":'<h3><a href="',
            "field":"url",
            "post":'">'
        },
        {
            "field":"name",
            "post":"</a></h3>"
        }
    ],
    [
        {
            "field":"description"
        },
        {
            "pre":' (created by <a href="/',
            "field":"owner",
            "post":'">'
        },
        {
            "field":"owner",
            "post":"</a>)"
        }
    ]
]

# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings
FACET_FIELD = ".exact"
MAPPINGS = {
    "record" : {
        "record" : {
            "date_detection" : "false",
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ]
        }
    },
    "collection" : {
        "collection" : {
            "date_detection" : "false",
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ]
        }
    }
},

# list of external sites to search for record data at    
SEARCHABLES = {
    "Google" : "http://www.google.com/search?q=",
    "Google scholar" : "http://scholar.google.com/scholar?q=",
    "Google video" : "http://www.google.com/search?tbm=vid&q=",
    "Google blogs" : "http://www.google.com/search?tbm=blg&q=",
    "Google books" : "http://www.google.com/search?tbm=bks&q=",
    "Google images" : "http://www.google.com/search?tbm=isch&q=",
    "Google search ResearcherID" : "http://www.google.com/search?q=XXXX+site%3Awww.researcherid.com",
    "Google search ACM Author Profiles" : "http://www.google.com/search?q=XXXX+ACM+author+profile+site%3Adl.acm.org",
    "Google search Mathemtatics Genealogy" : "http://www.google.com/search?q=XXXX+site%3Agenealogy.math.ndsu.nodak.edu",
    "Microsoft academic search" : "http://academic.research.microsoft.com/Search?query=",
    "Zentralblatt Math" : "http://www.zentralblatt-math.org/zmath/en/search/?q=",
    "Zentralblatt Math authors" : "http://www.zentralblatt-math.org/zmath/en/authors/?au=",
    "MathSciNet" : "http://www.ams.org/mathscinet-mref?ref=",
    "DOI resolver" : "http://dx.doi.org/",
    "PubMed" : "http://www.ncbi.nlm.nih.gov/pubmed?term=",
    "PubMed Central" : "http://www.ncbi.nlm.nih.gov/pmc/?term=",
    "BioMed Central" : "http://www.biomedcentral.com/search/results?terms="
}

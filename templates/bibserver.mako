<html>
<head>

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">
<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Nova+Square">

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.js"></script>
<script src="/static/bibsoup.js"></script>

<link rel="stylesheet" type="text/css" href="/static/bibsoup.css">
<link rel="stylesheet" type="text/css" href="/static/solreyes.css"/>

<title>BibSoup</title>

</head>

<body>

<div id="bibserver_container">


<div id="bibserver_header">
    <h1><a href="/">BibSoup</a></h1>
</div>

<div id="bibserver_search">
    <%include file="/search-box.mako"/>
</div>

    <div id="navigation">
        <%include file="/facet-extra.mako"/>
    </div>
    
    <div id="panel">
    
    % if c['results'].set_size() != 0:
        <span class="results_total">${c['results'].numFound()} results</span>
        <%include file="/paging.mako"/>
    % endif

    
    % if c['results'].set_size() == 0:
        No results
    % else:
        
        <!-- sorting and result sizes -->
        <%include file="/resultsperpage.mako"/>
        <%include file="/sort-options.mako"/>
        
        <!-- finally, the result set itself -->
        
        <%include file="/list-view.mako"/>
    
    % endif

    </div>

<div id="bibserver_vis">
    <p>...</p>
</div>

<%include file="/footer.mako"/>



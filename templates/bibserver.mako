<html>
<head>

<link rel="stylesheet" type="text/css" href="/static/bibsoup.css">

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.js"></script>

    <link rel="stylesheet" type="text/css" href="/static/solreyes.css"/>

    <script src="/static/bibsoup.js"></script>


    <title>${c['config'].service_name}</title>

</head>

<body>

<div id="bibserver_container">

<div id="bibserver_header">
    <h1><a href="/">BibSoup</a></h1>
    <p>all the world's research <span style="font-size:0.8em; padding:0 0 0 10px">(... or, as much as we can find)</span></p>
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


<div id="bibserver_footer">
    <ul>
    <li>BibSoup runs BibServer</li>
    <li><a href="http://bibserver.okfn.org">learn more about BibServer</a></li>
    <li><a href="http://bitbucket.org/okfn/bibserver">Get the code</a></li>
    </ul>
    
    <ul>
    <li>BibSoup is supported by</li>
    <li><a href="http://okfn.org">Open Knowledge Foundation</a></li>
    <li><a href="http://cottagelabs.com">Cottage Labs</a></li>
    <li></li>
</div>

</div>

</body>

</html>

<html>
<head>
    <link rel="stylesheet" type="text/css" href="/static/styless.css"/>
    <script type="text/javascript" src="/static/jquery.js"></script>
    <script>
    
    <%include file="/facets.js.mako"/>
    
    </script>
    <title>${c['config'].service_name}</title>
</head>

<body>
    
    <%include file="/header.mako"/>
    
    <div id="navigation">
        <%include file="/facet-extra.mako"/>
    </div>
    
    <div id="panel">
    
    % if c['results'].set_size() != 0:
        <%include file="/search-summary.mako"/>
        <%include file="/paging.mako"/>
    % endif

    
    % if c['results'].set_size() == 0:
        <%include file="/noresults.mako"/>
    % else:
        
        <!-- sorting and result sizes -->
        <%include file="/resultsperpage.mako"/>
        <%include file="/sort-options.mako"/>
        
        <!-- finally, the result set itself -->
        
        <%include file="/table-view.mako"/>
    
    % endif

    </div>
    
</body>
</html>
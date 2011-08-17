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
        <%include file="/branding.mako"/>
    </div>
    
    <div id="panel">
    
        <%include file="/implicit-title.mako"/>
        % if c['config'].allow_text_search:
            <%include file="/search-box.mako"/>
        % endif
        <%include file="/search-summary.mako"/>
            
        % if c['results'].set_size() == 0:
            <%include file="/noresults.mako"/>
        % else:
            <%include file="/sort-options.mako"/>
            <%include file="/paging.mako"/>
            <%include file="/resultsperpage.mako"/>
            <div class="result_view">
                <%include file="/${c['config'].result_view}"/>
            </div>
        
        % endif

    </div>
    
    <%include file="/footer.mako"/>
    
</body>
</html>
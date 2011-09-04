<html>
<head>
    <link rel="stylesheet" type="text/css" href="/static/styless.css"/>
    <script type="text/javascript" src="/static/jquery.js"></script>
    <script>
        
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
    
        <div class="implicit_title">
            % for field in c['implicit_facets'].keys():
                <h1>${c['config'].get_facet_display(field)} : ${", ".join([c['config'].get_value_display(field, x) for x in c['implicit_facets'][field]])}</h1>
            % endfor
        </div>

        % if c['config'].allow_text_search:
            <%include file="/search-box.mako"/>
        % endif
        <%include file="/search-summary.mako"/>
            
        % if c['results'].set_size() == 0:
          <div class="no_results">
          There are no results to display.
          </div>
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

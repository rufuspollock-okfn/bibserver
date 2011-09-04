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
  <div class="search_box">
      <form method="get" action="${c['url_manager'].get_search_form_action()}">
          <input type="text" name="q" value="${c['q']}"/>
          <input type="hidden" name="a" value="${c['url_manager'].get_form_field_args()}"/>
          <input type="submit" name="submit_search" value="Search"/>
      </form>
  </div>
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
        <div class="results_per_page">

          <div class="rpp_label">Show</div>
          % for rpp in c['config'].results_per_page_options:
          %   if rpp == c['results'].page_size():
              <div class="current_rpp">${rpp}</div>
          %   else:
              <div class="potential_rpp"><a href="${c['url_manager'].get_rpp_url(rpp)}">${rpp}</a></div>
          %   endif
          % endfor
        </div>

        <div class="spacer"></div>        

        <!-- finally, the result set itself -->        
        <%include file="/list-view.mako"/>
    
    % endif

    </div>

<div id="bibserver_vis">
    <p>...</p>
</div>

<%include file="/footer.mako"/>



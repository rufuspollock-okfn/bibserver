<html>
<head>

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">

<style type="text/css">
html, body{
    margin:0;
    padding:0;
    color:#373737;
    font-size:1.0em;
    font-family: 'Open Sans', sans-serif;
    text-shadow: 1px 1px 1px #aaa;
}
a{
    text-decoration:none;
    border-bottom:1px solid #ccc;
    color:#373737;
}
a:hover{
    color:red;
    border-bottom:1px solid red;
}
#bibserver_container{
    margin:0 auto 0 auto;
    width:800px;
    background:#fff;
    padding:0;
}
#bibserver_header{
    margin:-30px 0 20px 0;
    width:100%;
    text-align:center;
    padding:0;
   -moz-border-radius: 0 0 5px 5px;
    -webkit-border-radius: 0 0 5px 5px;
    border-radius: 0 0 5px 5px;
    -moz-box-shadow: 2px 2px 10px #373737;
    -webkit-box-shadow: 2px 2px 10px #373737;
    box-shadow: 2px 2px 10px #373737;
    background:#eee;
}
#bibserver_header h1{
    color:#373737;
    font-size:2em;
    padding:10px 0 0 0;
}
#bibserver_search{
    float:left;
    width:70%;
    margin:0 0 30px 0;
}
#bibsoup_searchbox{
    width:100%;
    height:40px;
    border:2px solid red;
   -moz-border-radius: 3px;
    -webkit-border-radius: 3px;
    border-radius: 3px;
    font-size:1.4em;
    margin:0;
}
#bibsoup_options{
    margin:0;
    float:left;
    width:30%;
    text-align:right;
}
#bibsoup_options ul{
    list-style-type:none;
    padding:0;
    margin:0 0 20px 0;
}
#bibserver_create{
    display:none;
}
#bibserver_vis{
    clear:both;
    width:100%;
    padding:30px 0 0 0;
}
#bibserver_footer{
    border:1px solid #ddd;
    width:100%;
    clear:both;
}
#bibserver_footer ul{
    float:left;
    list-style-type:none;
    padding:0 30px 0 0;
}
</style>

    <link rel="stylesheet" type="text/css" href="/static/styless.css"/>
    <script type="text/javascript" src="/static/jquery.js"></script>
    <script>
    
    <%include file="/facets.js.mako"/>
    
    </script>
    <title>${c['config'].service_name}</title>

</head>

<body>

<div id="bibserver_container">

<div id="bibserver_header">
    <h1><a href="/">BibSoup</a></h1>
    <p>all the world's research <span style="font-size:0.8em; padding:0 0 0 10px">(... or, as much as we can find)</span></p>
</div>

<div id="bibserver_search">
    <form action="/" method="POST">
    <input id="bibsoup_searchbox" type="text" name="q" value="${c['q']}" />
    </form>
</div>

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

<html>
<head>

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">
<link href='http://fonts.googleapis.com/css?family=Nova+Square' rel='stylesheet' type='text/css'>

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.js"></script>

<link rel="stylesheet" type="text/css" href="/static/bibsoup.css">


<script type="text/javascript">
jQuery(document).ready(function() {
    jQuery(window).load(function () {
        jQuery('#bibsoup_searchbox').focus();
    });
    if ( jQuery('#bibserver_msg').length ) {
        setTimeout( function() { jQuery('#bibserver_msg').hide('slow'); jQuery('#bibserver_msg').remove(); }, 20000 )
    }
});
</script>

</head>

<body>

<div id="bibserver_container">

<div id="bibserver_header">
    <h1><a href="/">BibSoup</a></h1>
    <p>all the world's research <span style="font-size:0.8em; padding:0 0 0 10px">(... or, as much as we can find)</span></p>
</div>

%if msg:
    <div id="bibserver_msg">
        <p> ${msg} </p>
    </div>
%endif

<div id="bibserver_search">
    <form action="/search" method="GET">
    <input id="bibsoup_searchbox" type="text" name="q" /><input id="bibsoup_searchsubmit" type="submit" name="submit" value="Search" />
    </form>
</div>

<div id="bibsoup_options">
    <ul>
    <li><a href="/content/caveat">ALPHA - caveats</a></li>
    <li><a href="/content/feedback">feedback - issues</a></li>
    <li><a href="">upload new collection</a></li>
    </ul>
</div>


<html>
<head>

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">
<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Nova+Square">

<link rel="stylesheet" type="text/css" href="/static/bibsoup.css">
<link rel="stylesheet" type="text/css" href="/static/solreyes.css"/>

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.js"></script>
<script src="/static/bibsoup.js"></script>

<title>BibSoup</title>

</head>

<body>

<div id="bibserver_container">

<div id="bibserver_header">
    <h1><a href="/">BibSoup</a></h1>
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
    </ul>
</div>


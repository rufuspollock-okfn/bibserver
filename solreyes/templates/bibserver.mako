<html>
<head>

<link rel="stylesheet" type="text/css" href="/static/bibsoup.css">

<link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open+Sans:300&v2">

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.js"></script>

    <link rel="stylesheet" type="text/css" href="/static/solreyes.css"/>

    <script type="text/javascript">

jQuery(document).ready(function() {

    // show full result content on title click
    var showall = function(event) {
        event.preventDefault();
        if ( $(this).hasClass('opened') ) {
            $(this).parent().siblings('.list_result_hidden').hide();
            $(this).removeClass('opened');
        } else {
            $(this).parent().siblings('.list_result_hidden').show();
            $(this).addClass('opened');
        }
    }
    jQuery('.list_result_field_showall').bind('click',showall);
    
    // do the facet list toggling
    var showfacets = function(event) {
        event.preventDefault();
        if ( $(this).hasClass('opened') ) {
            $(this).removeClass('opened');
            $(this).parent().siblings('.facet_value').hide('slow');
            $(this).children('.facet_pm').html('+&nbsp;');
        } else {
            $(this).addClass('opened');
            $(this).parent().siblings('.facet_value').show('slow');
            $(this).children('.facet_pm').html('-&nbsp;');
        }
    }
    jQuery(".facet_heading").bind('click',showfacets);

    // redesign results per page
    // build a list of acceptable rpp and the links to enable them
    var rpp = new Object();
    var rpp_label = jQuery('.rpp_label').html();
    var current_rpp = "";
    jQuery('.results_per_page').children().each(function() {
        if ( !jQuery(this).hasClass('rpp_label') ) {
            if ( jQuery(this).hasClass('current_rpp') ) {
                rpp[ jQuery(this).html() ] = "";
                current_rpp = jQuery(this).html();
            } else {
                rpp[ jQuery(this).children('a').html() ] = jQuery(this).children('a').attr('href');
            }
        }
    });
    // replace the rpp div with a selector
    var new_rpp = rpp_label + 'ing <select id="rpp_selector">';
    for (var item in rpp) {
        new_rpp += '<option value="' + rpp[item] + '"';
        if ( item == current_rpp ) {
            new_rpp += ' "selected"';
        }
        new_rpp += '>' + item + '</option>';
    }
    new_rpp += '</select> per page.';
    jQuery('.results_per_page').html(new_rpp);
    // attach functionality to trigger rpp selections
    var rpp_select = function(event) {
        event.preventDefault();
        if ( jQuery(this).val() != "" ) {
            window.location = jQuery(this).val();
        }
    }
    jQuery('#rpp_selector').bind('change',rpp_select);
    
    // redesign paging
    // build a list of paging options and links to enable them
    var paging = new Object();
    var paging_label = jQuery('.paging_label').html();
    var current_page = "";
    jQuery('.paging').children().each(function() {
        if ( !jQuery(this).hasClass('paging_label') ) {
            if ( jQuery(this).hasClass('current_page') ) {
                paging[ jQuery(this).html() ] = "";
                current_page = jQuery(this).html();
            } else {
                paging[ jQuery(this).children('a').html() ] = jQuery(this).children('a').attr('href');
            }
        }
    });
    // replace the paging div with a selector
    var new_paging = paging_label + " " + '<select id="paging_selector">';
    for (var item in paging) {
        new_paging += '<option value="' + paging[item] + '"';
        if ( item == current_page ) {
            new_paging += "selected";
        }
        new_paging += '>' + item + '</option>';
    }
    new_paging += '</select> of ' + jQuery('.results_total').html().replace(" results",". &nbsp;&nbsp;&nbsp;&nbsp;");
    jQuery('.results_total').remove();
    jQuery('.paging').html(new_paging);
    // attach functionality to trigger paging selections
    var page_select = function(event) {
        event.preventDefault();
        if ( jQuery(this).val() != "" ) {
            window.location = jQuery(this).val();
        }
    }
    jQuery('#paging_selector').bind('change',page_select);
    
    // redesign facet headers if they have no further options
    jQuery('.facet').each(function() {
        if ( jQuery(this).children().last().children().size() < 1 ) {
            jQuery(this).children('.facet_heading').children('a').children('.facet_pm').remove();
            var title = jQuery(this).children('.facet_heading').children('a').html();
            var standard = '<strong>' + title + '</strong>';
            jQuery(this).children('.facet_heading').html(standard)
        }
    });
    
});

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

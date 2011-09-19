
jQuery(document).ready(function() {

    // enable show of upload from PC on upload page
    jQuery('#frompc').hide();
    var showfrompc = function(event) {
        event.preventDefault();
        if ( $(this).hasClass('opened') ) {
            $('#frompc').hide();
            $('#fromurl').show();
            $(this).removeClass('opened');
            $(this).html("upload from your PC");
        } else {
            $('#fileformat').hide();
            $('#fromurl').hide();
            $('#frompc').show();
            $(this).addClass('opened');
            $(this).html("upload from URL");
        }
    }
    jQuery('.frompc').bind('click',showfrompc);
    
    // enable request for format type, when format type is unknown, on upload page
    jQuery('#fileformat').hide();
    var checkformat = function(event) {
        event.preventDefault();
        $('#fileformat').hide();
        var value = $(this).val();
        if (    value.substr(-4) != ".bib" && 
                value.substr(-7) != ".bibtex" && 
                value.substr(-4) != ".csv" && 
                value.substr(-8) != ".bibjson" && 
                value.substr(-5) != ".json"
                ) {
            $('#fileformat').show('fast');
        }
    }
    jQuery('.sourcefile').bind('change',checkformat)
    

    // if there is a msg, display and then hide after delay
    if ( jQuery('#bibserver_msg').length ) {
        setTimeout( function() { jQuery('#bibserver_msg').hide('slow'); jQuery('#bibserver_msg').remove(); }, 20000 )
    }

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

    // add external search autocomplete box
    var searchables = {
        "Google" : "http://www.google.com/search?q=",
        "Google scholar" : "http://scholar.google.com/scholar?q=",
        "Google video" : "http://www.google.com/search?tbm=vid&q=",
        "Google blogs" : "http://www.google.com/search?tbm=blg&q=",
        "Google books" : "http://www.google.com/search?tbm=bks&q=",
        "Google images" : "http://www.google.com/search?tbm=isch&q=",
        "Google + ResearcherID" : "http://www.google.com/search?q=XXXX+site%3Awww.researcherid.com",
        "Google + ACM Author Profiles" : "http://www.google.com/search?q=XXXX+ACM+author+profile+site%3Adl.acm.org",
        "Google + Mathemtatics genealogy" : "http://www.google.com/search?q=XXXX+site%3Agenealogy.math.ndsu.nodak.edu",
        "Microsoft academic search" : "http://academic.research.microsoft.com/Search?query=",
        "Bing" : "http://www.bing.com/search?q=",
        "Bing images" : "http://www.bing.com/images/search?q=",
        "Bing + author" : "http://www.bing.com/search?q=XXXX+author",
        "Bing + ResearcherID" : "http://www.bing.com/search?q=XXXX+site%3Aresearcherid.com",
        "Homepage Seer" : "http://thelma.ist.psu.edu/search.php?q=",
        "Zentralblatt Math" : "http://www.zentralblatt-math.org/zmath/en/search/?q=",
        "Zentralblatt Math authors" : "http://www.zentralblatt-math.org/zmath/en/authors/?au=",
        "MathSciNet HTML" : "http://www.ams.org/mathscinet-mref?dataType=mathscinet&ref=",
        "MathSciNet BibTex" : "http://www.ams.org/mathscinet-mref?mref-submit=Search&dataType=bibtex&ref="          
    }
    jQuery('.viewrecord').each(function(index) {
        var searcher = '<span id="ext_srch_' + index + '"> or search <select class="extsrch_target">';
        for (var item in searchables) { searcher += '<option value="' + searchables[item] + '">' + item + '</option>'; }
        searcher += '</select> for <input class="extsrch_value" id="extsrch_value_' + index + '" />';
        searcher += '<a href="" alt="find it" title="find it" class="submit_extsrch btn">go</a></span>';
        jQuery(this).after(searcher);
        var tags = [];
        jQuery(this).parent().prev('table').find('tr').each(function() {
            var thing = jQuery(this).children().last().html().replace(/<.*?>/ig,'');
            if ( thing != "" && thing != null ) {
                tags.push(thing);
            }
        });
        jQuery('#extsrch_value_' + index).autocomplete({source:tags});
    });
    var dosearch = function(event) {
        var target = jQuery(this).siblings('.extsrch_target').val();
        var value = jQuery(this).siblings('.extsrch_value').val();
        if ( target.match("XXXX") ) {
            var href = target.replace("XXXX",value);
        } else {
            var href = target + value;
        }
        jQuery(this).attr('href',href);
    }
    jQuery('.submit_extsrch').bind('click',dosearch);

    // attach functionality to trigger rpp, page, sort selections
    jQuery('#paging_trigger').remove();
    var rpp_select = function(event) {
        jQuery('#page_select').val($("#page_select option:first").val());
        jQuery(this).closest('form').trigger('submit');
    }
    var page_select = function(event) {
        jQuery(this).closest('form').trigger('submit');
    }
    jQuery('#rpp_select').bind('change',rpp_select);
    jQuery('#sort_select').bind('change',rpp_select);
    jQuery('#order_select').bind('change',rpp_select);
    jQuery('#page_select').bind('change',page_select);

    
    // do the facet list toggling
    jQuery('.facet_value').hide();
    var showfacets = function(event) {
        event.preventDefault();
        if ( $(this).hasClass('opened') ) {
            $(this).removeClass('opened');
            $(this).parent().siblings('.facet_value').hide('slow');
            $(this).siblings().next('.facet_sorting').hide('slow');
            $(this).children('.facet_pm').html('+&nbsp;');
        } else {
            $(this).addClass('opened');
            $(this).parent().siblings('.facet_value').show('slow');
            $(this).siblings().next('.facet_sorting').show('slow');
            $(this).children('.facet_pm').html('-&nbsp;');
        }
    }
    jQuery(".facet_heading").bind('click',showfacets);

    // redesign facet headers if they have no further options
    jQuery('.facet').each(function() {
        if ( jQuery(this).children().last().children().size() < 2 ) {
            jQuery(this).children('.facet_heading').children('a').children('.facet_pm').remove();
            var title = jQuery(this).children('.facet_heading').children('a').html();
            var standard = '<strong>' + title + '</strong>';
            jQuery(this).children('.facet_heading').html(standard)
        }
    });
    
    // add in-page sorting to the facet selections
    var sorts = '<a class="facet_sorting btn info" href="">a-z | hi-lo</a>';
    jQuery('div.facet_selected').after(sorts);
    jQuery('.facet_sorting').hide();
    var dosort = function(event) {
        event.preventDefault();
        if (jQuery(this).hasClass('sorted')) {
            if (jQuery(this).hasClass('reversed')) {
                if (jQuery(this).hasClass('numbered')) {
                    jQuery(this).next('ul.facet_value').children().tsort("span.count",{order:'desc'});
                    jQuery(this).removeClass('numbered');
                    jQuery(this).removeClass('reversed');
                    jQuery(this).removeClass('sorted');
                } else {
                    jQuery(this).next('ul.facet_value').children().tsort("span.count");
                    jQuery(this).addClass('numbered');
                }
            } else {
                jQuery(this).next('ul.facet_value').children().tsort({order:'desc'});
                jQuery(this).addClass('reversed');
            }
        } else {
            jQuery(this).next('ul.facet_value').children().tsort();
            jQuery(this).addClass('sorted');
        }
    }
    jQuery('.facet_sorting').bind('click',dosort);

    
});



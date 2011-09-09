
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

    // attach functionality to trigger rpp and page selections
    jQuery('#paging_trigger').remove();
    var rpp_select = function(event) {
        jQuery('#page_select').val($("#page_select option:first").val());
        jQuery(this).closest('form').trigger('submit');
    }
    var page_select = function(event) {
        jQuery(this).closest('form').trigger('submit');
    }
    jQuery('#rpp_select').bind('change',rpp_select);
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




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
    
    // search for collection id related to source on upload page
    var findcoll = function(event) {
        jQuery.ajax({
            url: '/collections.json?q=source:"' + jQuery(this).val() + '"'
            , type: 'GET'
            , success: function(json, statusText, xhr) {
                if (json.records.length != 0) {
                    if (json.records[0]['owner'] == jQuery('#current_user').val()) {                    
                        jQuery('#collection').val(json.records[0]['id']);
                    }
                }
            }
            , error: function(xhr, message, error) {
            }
        });
    }
    jQuery('.sourcefile').bind('keyup',findcoll)

    // search for collection id similar to that provided, and warn of duplicates controlled by third parties
    var checkcoll = function(event) {
        jQuery.ajax({
            url: '/collections.json?q=id:"' + jQuery(this).val() + '"'
            , type: 'GET'
            , success: function(json, statusText, xhr) {
                if (json.records.length != 0) {
                    if (json.records[0]['owner'] != jQuery('#current_user').val()) {
                        if (jQuery('#collwarning').length == 0) {
                            var where = json.records[0]['owner'] + '/' + json.records[0]['id']
                            jQuery('#collection').after('&nbsp;&nbsp;<span id="collwarning" class="label warning"><a href="/' + where + '">sorry, in use</a>. Please change.</span>');
                        }
                    }
                } else {
                    jQuery('#collwarning').remove();
                }
            }
            , error: function(xhr, message, error) {
            }
        });
        
    }
    jQuery('#collection').bind('keyup',checkcoll);

    // show search options
    if ( jQuery('input[name="showopts"]').val() != undefined && jQuery('input[name="showopts"]').val() != "" ) {
        jQuery('#search_options').addClass('shown').show();
    }
    var show_search_options = function(event) {
        event.preventDefault();
        if ( jQuery('#search_options').hasClass('shown') ) {
            jQuery('#search_options').removeClass('shown').hide();
            jQuery('input[name="showopts"]').remove();
        } else {
            jQuery('#search_options').addClass('shown').show();
            if ( jQuery('input[name="showopts"]').val() == undefined) {
                jQuery('form').append('<input type="hidden" name="showopts" value="true" />');
            }
        }
    }
    jQuery('#show_search_options').bind('click',show_search_options);


    var show_view_options = function(event) {
        event.preventDefault();
        if (jQuery('.view_options').hasClass('shown')) {
            jQuery('.view_options').removeClass('shown').hide();
        } else {
            jQuery('.view_options').addClass('shown').show();
        }
    }
    jQuery('#show_view_options').bind('click',show_view_options);



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

    // do search options
    var fixmatch = function(event) {
        event.preventDefault();
        if ( jQuery(this).attr('id') == "partial_match" ) {
            var newvals = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').replace(/\~/gi,'').split(' ');
            var newstring = "";
            for (item in newvals) {
                if (newvals[item].length > 0 && newvals[item] != ' ') {
                    if (newvals[item] == 'OR' || newvals[item] == 'AND') {
                        newstring += newvals[item] + ' ';
                    } else {
                        newstring += '*' + newvals[item] + '* ';
                    }
                }
            }
            jQuery('#searchbox').val(newstring);
        } else if ( jQuery(this).attr('id') == "fuzzy_match" ) {
            var newvals = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').replace(/\~/gi,'').split(' ');
            var newstring = "";
            for (item in newvals) {
                if (newvals[item].length > 0 && newvals[item] != ' ') {
                    if (newvals[item] == 'OR' || newvals[item] == 'AND') {
                        newstring += newvals[item] + ' ';
                    } else {
                        newstring += newvals[item] + '~ ';
                    }
                }
            }
            jQuery('#searchbox').val(newstring);
        } else if ( jQuery(this).attr('id') == "exact_match" ) {
            var newvals = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').replace(/\~/gi,'').split(' ');
            var newstring = "";
            for (item in newvals) {
                if (newvals[item].length > 0 && newvals[item] != ' ') {
                    if (newvals[item] == 'OR' || newvals[item] == 'AND') {
                        newstring += newvals[item] + ' ';
                    } else {
                        newstring += '"' + newvals[item] + '" ';
                    }
                }
            }
            $.trim(newstring,' ');
            jQuery('#searchbox').val(newstring);
        } else if ( jQuery(this).attr('id') == "match_any" ) {
            jQuery('#default_operator').remove();
            if (jQuery(this).hasClass('match_all')) {
                jQuery('#searchform').append('<input type="hidden" id="default_operator" name="default_operator" value="OR" />');
                jQuery('#searchbox').val(jQuery.trim(jQuery('#searchbox').val().replace(/ AND /gi,' ')));
                jQuery('#searchbox').val(jQuery('#searchbox').val().replace(/ /gi,' OR '));
            } else {
                jQuery('#searchbox').val(jQuery.trim(jQuery('#searchbox').val().replace(/ OR /gi,' ')));
                jQuery('#searchbox').val(jQuery('#searchbox').val().replace(/ /gi,' AND '));
            }
        }
        jQuery('#submit_main_search').trigger('click');
    }
    jQuery('#partial_match').bind('click',fixmatch);
    jQuery('#exact_match').bind('click',fixmatch);
    jQuery('#fuzzy_match').bind('click',fixmatch);
    jQuery('#match_any').bind('click',fixmatch);
    
    var search_key = function(event) {
        event.preventDefault();
        var val = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').replace(/.*\.exact:/,'');
        if ( !(val[0] == '"' && val[val.length-1] == '"') ) {
            val = '"' + val + '"';
        }
        jQuery('#searchbox').val(jQuery(this).val() + ':' + val);
        jQuery('#submit_main_search').trigger('click');
    }
    jQuery('#search_key').bind('change',search_key);
    
    // In ticket view, bind a click event to reset buttons to allow re-import of upload tickets
    jQuery('.reset_ticket').click(function(event) {
        event.preventDefault();
        var ticket_id = jQuery(this).attr('href');        
        jQuery.post('/ticket/'+ticket_id+'/reset', function(data) {
            document.location.reload();
        });
    });
    
    // click event for deleting tickets
    jQuery('.delete_ticket').click(function(event) {
        event.preventDefault();
        var ticket_id = jQuery(this).attr('href');        
        jQuery.post('/ticket/'+ticket_id+'/delete', function(data) {
            document.location = '/ticket/';
        });
    });
});



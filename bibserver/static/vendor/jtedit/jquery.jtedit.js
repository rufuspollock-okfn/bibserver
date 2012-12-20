/*
 * jquery.jtedit.js
 *
 * a tool for neatly displaying JSON objects
 * and allowing edit of them
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2012. http://copyheart.org
 *
 */

// first define the bind with delay function from (saves loading it separately) 
// https://github.com/bgrins/bindWithDelay/blob/master/bindWithDelay.js
(function($) {
    $.fn.bindWithDelay = function( type, data, fn, timeout, throttle ) {
    var wait = null;
    var that = this;

    if ( $.isFunction( data ) ) {
        throttle = timeout;
        timeout = fn;
        fn = data;
        data = undefined;
    }

    function cb() {
        var e = $.extend(true, { }, arguments[0]);
        var throttler = function() {
            wait = null;
            fn.apply(that, [e]);
            };

            if (!throttle) { clearTimeout(wait); }
            if (!throttle || !wait) { wait = setTimeout(throttler, timeout); }
        }

        return this.bind(type, data, cb);
    }
})(jQuery);


(function($){
    $.fn.jtedit = function(options) {

        // specify the defaults
        var defaults = {
            "makeform": true,                   // whether or not to build the form first
            "actionbuttons": true,              // whether or not to show action buttons
            "jsonbutton": true,                 // show json button or not (alt. for these is write the buttons yourself)
            "source":undefined,                 // a source from which to GET the JSON data object
            "target": window.location,          // a target to which updated JSON should be POSTed
            "reloadonsave": window.location,    // if this has value, page reload will be triggered to location specified here after save
            "reloadondelete": window.location,  // where to redirect to after deleting
            "savemsg":"changes saved",          // alert message on save change, if any
            "saveonupdate":false,               // whether to auto-save on any update
            "delmsg":"record deleted",          // alert message on record delete, if any
            "datatype":"json",                  // JSON or JSONP depending on target location
            "data":{"test":"data"},             // a JSON object to render for editing
            "addable":{},                       // things that should be provided as addables to the item
            "customadd": true,                  // whether or not user can specify new items
            "tags": []
        };

        // add in any overrides from the call
        $.fn.jtedit.options = $.extend(defaults,options);
        var options = $.fn.jtedit.options;

        // ===============================================        
                
        // visualise the data values onto the page form elements
        // and create the form elements in the process if necessary
        var dovisify = function(first) {
            var visify = function(data,route) {
                for (var key in data) {
                    route == undefined ? thisroute = key : thisroute = route + '_' + key;
                    if ( typeof(data[key]) == 'object' ) {
                        visify(data[key],thisroute);
                    } else {
                        options.makeform ? $('#jtedit').append('<input type="text" class="jtedit_value jtedit_' + thisroute + '" />') : "";
                        $('.jtedit_' + thisroute).val( data[key] );
                    };
                };
            };
            visify( options.data );
            if ( options.makeform ) {
                $('.jtedit_value').autoResize({minHeight: 20, maxHeight:600, minWidth:50, maxWidth: 300, extraSpace: 5});
                $('.jtedit_value').bind('mouseup',selectall);
                options.makeform = false;
            }
            if ( first ) {
                $('.jtedit_value').bind('blur',updates);
                $('.jtedit_value').bindWithDelay('keyup',updates,1000);
                $('#jtedit_json').val(JSON.stringify(options.data,"","    "));
            } else {
                updates();
            };
        };


        // parse visualised values from the page
        var parsevis = function() {
            function parser(scope, path, value) {
                var i = 0, lim = path.length;
                for (; i < lim; i += 1) {
                    if (typeof scope[path[i]] === 'undefined') {
                        !isNaN(parseInt(path[i+1])) ? scope[path[i]] = [] : scope[path[i]] = {};
                    };
                    i === lim - 1 ? scope[path[i]] = value : scope = scope[path[i]];
                };
            };
            var scope = {};
            $('.jtedit_value').each(function() {
                if ( $(this).attr('data-path') !== undefined ) {
                    var path = $(this).attr('data-path').split(/\./);
                } else {
                    var classes = $(this).attr('class').split(/\s+/);
                    for ( var cls in classes ) {
                        if ( classes[cls].indexOf('jtedit_') == 0 && classes[cls] != 'jtedit_value' ) {
                            var path = classes[cls].split('_').slice(1);
                            break;
                        };
                    };
                };
                parser(scope, path, $(this).val());
            });
            options.data = $.extend(true,options.data,scope);
        }
        
        // ===============================================
        
        // update JSON when changes occur on visual display
        var updates = function(event) {
            parsevis();
            $('#jtedit_json').val(JSON.stringify(options.data,"","    "));
            options.saveonupdate ? $.fn.jtedit.saveit() : "";
        };
        
        // update visual display when raw JSON updated
        var editjson = function(event) {
            options.data = $.parseJSON($('#jtedit_json').val());
            options.saveonupdate ? $.fn.jtedit.saveit() : "";
            dovisify();
        };

        // select all in input / textarea
        var selectall = function(event) {
            event.preventDefault();
            $(this).select();
        };

        // show raw json on request
        var jtedit_json = function(event) {
            event.preventDefault();
            $('#jtedit_json').toggle();
        };
        
        // ===============================================

        // create the plugin on the page
        return this.each(function() {

            obj = $(this);

            $('#jtedit',obj).remove();
            $(obj).append('<div id="jtedit" class="clearfix"></div>');
            var actions = '';
            if ( options.jsonbutton ) { actions += '<div class="jtedit_actions"><a class="btn jtedit_json" href="">show JSON</a>'; };
            if ( options.actionbuttons ) {
                actions += ' <a class="jtedit_saveit btn btn-primary" href="save"><i class="icon-check icon-white"></i> save</a> ' + 
                '<a class="jtedit_deleteit btn btn-danger" href=""><i class="icon-remove icon-white"></i> delete</a>';
            };
            actions += '</div>';
            $('#jtedit').append( actions + '<div id="jtedit_visual"></div><div><textarea id="jtedit_json"></textarea></div>' );
                        
            $('#jtedit_json').autoResize({minHeight: 150, maxHeight:500, minWidth:50, maxWidth: 500, extraSpace: 5});
            $('#jtedit_json').hide();
            $('#jtedit_json').bind('blur',editjson);
            
            $('.jtedit_saveit').bind('click',$.fn.jtedit.saveit);
            $('.jtedit_deleteit').bind('click',$.fn.jtedit.deleteit);
            $('.jtedit_json').bind('click',jtedit_json);
            
            if (options.source) {
                $.ajax({
                    url: options.source
                    , type: 'GET'
                    , success: function(data, statusText, xhr) {
                        options.data = data
                        dovisify(true)
                    }
                    , error: function(xhr, message, error) {
                        options.source = false
                        alert("Sorry. Your data could not be parsed from " + sourceurl)
                    }
                });
            } else {
                dovisify(true);
            };

        });

    };
    
    $.fn.jtedit.saveit = function(refresh,event,data) {
        event ? event.preventDefault() : "";
        var options = $.fn.jtedit.options;
        !data ? data = $.parseJSON(jQuery('#jtedit_json').val()) : false;
        !options.target ? options.target = prompt('Please provide URL to save this record to:') : false;
        if (options.target) {
            $.ajax({
                url: options.target
                , type: 'POST'
                , data: JSON.stringify(data)
                , contentType: "application/json; charset=utf-8" 
                , dataType: options.datatype
                , processData: false
                , success: function(data, statusText, xhr) {
                    options.savemsg ? alert(options.savemsg) : ""
                    options.reloadonsave ? window.location = options.reloadonsave : ""
                    refresh ? window.location = "" : ""
                }
                , error: function(xhr, message, error) {
                    alert("Error... " + error)
                }
            });
        } else {
            alert('No suitable URL to save to was provided');
        };
    };

    $.fn.jtedit.deleteit = function(event) {
        event ? event.preventDefault() : "";
        var options = $.fn.jtedit.options;
        if (!options.target) {
            alert('There is no available source URL to delete from');
        } else {
            var confirmed = confirm("You are about to delete this record. Are you sure you want to do so?");
            if (confirmed) {
                $.ajax({
                    url: options.target
                    , type: 'DELETE'
                    , success: function(data, statusText, xhr) {
                        options.delmsg ? alert(options.delmsg) : ""
                        options.reloadondelete ? window.location = options.reloadondelete : ""
                    }
                    , error: function(xhr, message, error) {
                        alert("Error... " + error)
                    }
                });
            };
        };
    };

    $.fn.jtedit.options = {};
    
})(jQuery);





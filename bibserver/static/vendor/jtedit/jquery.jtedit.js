/*
 * jquery.jtedit.js
 *
 * a tool for displaying JSON objects as a table
 * and allowing edit of them
 *
 * open source license - cc-by
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
*/

// include css
//<![CDATA[
/*if(document.createStyleSheet) {
    document.createStyleSheet('http://test.cottagelabs.com/jtedit/jtedit.css');
} else {
    var styles = "@import url('http://test.cottagelabs.com/jtedit/jtedit.css');";
    var newSS = document.createElement('link');
    newSS.rel = 'stylesheet';
    newSS.href = 'data:text/css,'+escape(styles);
    document.getElementsByTagName("head")[0].appendChild(newSS);    
}
//]]>*/


(function($){
    $.fn.jtedit = function(options) {

        // specify the defaults
        var defaults = {
            "edit":true,                    // whether or not to make the table editable
            "source":undefined,             // a source from which to GET the JSON data object
            "target":undefined,             // a target to which updated JSON should be POSTed
            "noedit":[],                    // a list of keys that should not be editable, when edit is enabled
            "data":undefined    // a JSON object to render for editing
        };

        // add in any overrides from the call
        var options = $.extend(defaults,options);

        // add in any options from the query URL
        var geturlparams = function() {
            var vars = [], hash;
            var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
            for (var i = 0; i < hashes.length; i++) {
                    hash = hashes[i].split('=');
                    vars.push(hash[0]);
                    if (!(hash[1] == undefined)) {
                        hash[1] = unescape(hash[1]);
                        if (hash[0] == "source") {
                            hash[1] = hash[1].replace(/"/g,'');
                        } else if (hash[0] == "data") {
                            hash[1] = $.parseJSON(hash[1]);
                        }
                    }
                    vars[hash[0]] = hash[1];
            }
            return vars;
        }
        $.extend(options,geturlparams());


        // ===============================================
        // create a pretty table out of JSON
        var tablify = function(data,edit) {
            if (edit == undefined) {
                edit = true;
            }
            if (data == null) {
                data = "";
            }
            var s = "";
            if (typeof(data) == 'object') {
                s = '<table';
                if (data.constructor.toString().indexOf("Array") != -1) {
                    s += ' class="jtedit_listtable"';
                }
                s += '><tbody>';
                for (var key in data) {
                    var loopedit = edit;
                    if ($.inArray(key,options.noedit) != -1) {
                        loopedit = false;
                    }
                    s += '<tr><td>';
                    if (data.constructor.toString().indexOf("Array") == -1) {
                        s += '<input type="text" class="jtedit jtedit_key" value="' + key + '" ';
                        if (!loopedit) {
                            s += 'disabled="disabled" ';
                        }
                        s += '/>'
                    }
                    s += tablify(data[key],loopedit);
                    s += '</td></tr>';
                }
                s += '</tbody></table>';
            } else {
                if (data.length > 30 && edit) {
                    s += '<textarea ';
                    if (!edit) {
                        s += 'disabled="disabled" ';
                    }
                    s += 'class="jtedit jtedit_field">' + data + '</textarea>';
                } else {
                    s += '<input type="text" class="jtedit jtedit_field" value="' + data + '" ';
                    if (!edit) {
                        s += 'disabled="disabled" ';
                    }
                    s += '/>';
                }
            }
            return s;
        }


        // ===============================================
        // parse a pretty table into JSON
        var parsetable = function(table) {
            if (table == undefined) {
                var table = $('table');
            }
            if (table.children('tbody').first().children('tr').first().children('td').children('.jtedit_key').length) {
                var json = {};
            } else {
                var json = [];
            }
            table.children('tbody').first().children('tr').each(function() {
                var val = "";
                if ($(this).children('td').children('table').length) {
                    val = parsetable($(this).children('td').children('table'));
                } else {
                    val = $(this).children('td').children('.jtedit_field').val();
                }
                if ($(this).children('td').children('.jtedit_key').length) {
                    json[$(this).children('td').children('.jtedit_key').val()] = val;
                } else {
                    if (val != undefined) {
                        if (val.length > 0 || typeof(val) == 'object') {
                            json.push(val);
                        }
                    }
                }
            });
            return json;
        }
        
        // make everything in the JSON texbox selected by default
        var selectall = function(event) {
            $(this).select();
        }
        // prevent unselect on chrome mouseup
        var selectallg = function(event) {
            event.preventDefault();
        }


        // ===============================================
        // key and field option and edit triggers
        var opts = function(event) {
            $('tr').removeClass('jtedit_focus');
            $(this).closest('tr').addClass('jtedit_focus');
            var left = $(this).closest('tr').offset().left + $(this).closest('tr').width() + 30;
            var top = $(this).offset().top;
            if (false) {
                $('.jtedit_field_opts').hide();
            } else {
                $('.jtedit_field_opts').show();
            }
            $('#jtedit_menu').offset({"top":top,"left":left}).show();
            $(this).select();
        }
        var updates = function(event) {
            $('#jtedit_json').val(JSON.stringify(parsetable(),"","    "));
            $(this).removeClass('text_empty');
            if ($(this).val() == "") {
                $(this).addClass('text_empty');
            }
        }


        // ===============================================
        // action button functions        
        var jtedit_json = function(event) {
            event.preventDefault();
            if ($(this).hasClass('showing')) {
                $(this).removeClass('showing').html('show JSON');
                $('#jtedit_json').hide();
            } else {
                $(this).addClass('showing').html('hide JSON');
                $('#jtedit_json').show();
            }
        }

        var jtedit_delete = function(event) {
            event.preventDefault();
            if ($('.jtedit_focus').siblings().length == 0) {
                if ($('.jtedit_focus').children('td').children('.jtedit_key').length || $('.jtedit_focus').parent().parent('table').hasClass('jtedit_listtable')) {
                    $('.jtedit_focus').closest('table').replaceWith('<input type="text" class="jtedit jtedit_field" />');
                    jtedit_bindings();
                } else {
                    $('.jtedit_focus').replaceWith('<tr><td><input type="text" class="jtedit jtedit_field" /></td></tr>');
                    jtedit_bindings();
                }
            } else {
                $('.jtedit_focus').remove();
            }
            $('#jtedit_json').val(JSON.stringify(parsetable(),"","    "));
        }

        var jtedit_minimise = function(event) {
            event.preventDefault();
            if ($('.jtedit_focus').hasClass('jtedit_minned')) {
                $('.jtedit_focus').removeClass('jtedit_minned');
                $('.jtedit_focus').children('td').children('.jtedit_mindots').remove();
                $('.jtedit_focus').children('td').children().show();
                var left = $('.jtedit_focus').offset().left + $('.jtedit_focus').width() + 10;
                $('#jtedit_menu').offset({"left":left}).show();
            } else {
                $('.jtedit_focus').addClass('jtedit_minned');
                $('.jtedit_focus').children('td').children().hide();
                $('.jtedit_focus').children('td').first().children().first().show().after('<span class="jtedit_mindots">(...)</span>');
            }
        }
        var jtedit_minall = function(event) {
            event.preventDefault();
            $('table table').children('tbody').children('tr').addClass('jtedit_minned');
            $('table table').hide();
        }
        var jtedit_maxall = function(event) {
            event.preventDefault();
            $('table table').children('tbody').children('tr').removeClass('jtedit_minned');
            $('table table').show();
        }        
        
        var jtedit_addrow = function(event) {
            event.preventDefault();
            var inputcount = $('.jtedit_focus').children('td').children('input').length;
            var tablecount = $('.jtedit_focus').children('td').children('table').length;
            if (inputcount == 2 || inputcount + tablecount == 2) {
                $('.jtedit_focus').after('<tr><td><input type="text" class="jtedit jtedit_key text_empty" /><input type="text" class="jtedit jtedit_field text_empty" /></td></tr>');
                
            } else {
                $('.jtedit_focus').after('<tr><td><input type="text" class="jtedit jtedit_field text_empty" /></td></tr>');
            }
            $('.jtedit_focus').next().find('input').autoResize({"minWidth": 60,"maxWidth": 500,"minHeight": 20,"maxHeight": 200,"extraSpace": 10});
            $('.jtedit_focus').next().find('input').bind('blur',updates).bind('focus',opts).bind('mouseup',selectallg);
        }
        
        var jtedit_list = function(event) {
            event.preventDefault();
            var field = $('.jtedit_focus').children('td').children('.jtedit_field');
            field.replaceWith('<table class="jtedit_listtable"><tbody><tr><td><input type="text" class="jtedit jtedit_field text_empty" /></td></tr></tbody></table>');
            $('.jtedit_focus').children('td').find('input').autoResize({"minWidth": 60,"maxWidth": 500,"minHeight": 20,"maxHeight": 200,"extraSpace": 10});
            $('.jtedit_focus').children('td').find('input').bind('focus',opts).bind('blur',updates).bind('mouseup',selectallg);
        }
        var jtedit_object = function(event) {
            event.preventDefault();
            var field = $('.jtedit_focus').children('td').children('.jtedit_field');
            field.replaceWith('<table><tbody><tr><td><input type="text" class="jtedit jtedit_key text_empty" /><input type="text" class="jtedit jtedit_field text_empty" /></td></tr></tbody></table>');
            $('.jtedit_focus').children('td').find('input').autoResize({"minWidth": 60,"maxWidth": 500,"minHeight": 20,"maxHeight": 200,"extraSpace": 10});
            $('.jtedit_focus').children('td').find('input').bind('focus',opts).bind('blur',updates).bind('mouseup',selectallg);
        }
        
        var jtedit_save = function(event) {
            event.preventDefault();
            alert("ah hah! I don't do anything yet. soon you will be able to save back to some resource. For now, just use the show JSON button and copy and paste the changes from there to wherever you want them.");
        }
        
        var jtedit_nohelp = function(event) {
            event.preventDefault();
            $('#jtedit_help').remove();
        }
        var jtedit_help = function(event) {
            event.preventDefault();
            $('#jtedit').append(jtedit_help_content);
            $('.jtedit_nohelp').bind('click',jtedit_nohelp);
        }

        var jtedit_nomenu = function(event) {
            event.preventDefault();
            $('.jtedit_focus').removeClass('jtedit_focus');
            $('#jtedit_menu').offset({"top":0,"left":0}).hide();
        }


        // ===============================================
        // get data from a source URL
        var data_from_source = function(sourceurl) {
            $.ajax({
                url: sourceurl
                , type: 'GET'
                , success: function(data, statusText, xhr) {
                    if (!(data.responseText == undefined)) {
                        data = data.responseText;
                        data = data.replace(/[\r|\n]+/g,'');
                        data = data.replace(/^.*?(?={)/,'').replace(/[^}]+$/,'');
                        data = data.replace('</p>','').replace('</p>','');
                        data = $.parseJSON(data);
                    }
                    options.data = data;
                    $('#jtedit').prepend(tablify(options.data,options.edit));
                    jtedit_bindings();
                    $('#jtedit_json').val(JSON.stringify(parsetable(),"","    "));
                }
                , error: function(xhr, message, error) {
                    alert("Sorry. Your data could not be parsed from " + sourceurl + ". Please try again, or paste your data into the provided field.");
                    console.error("Error while loading data from ElasticSearch", message);
                    throw(error);
                }
            });
        }

        // get data from the user
        var data_from_user = function() {
            var fromuser = '<div id="jtedit_fromuser"><h2>jtedit</h2><p>A nice easy JSON editor.</p>' +
                '<p>Please provide some JSON you want to edit. Either input the web address of a JSON file, or paste your JSON in the box below.</p>' +
                '<p>(Note that for a web address, it must be a file that actually identifies as JSON, not just a text file that has JSON in it.' +
                ' If you have a JSON file you would like to edit that does not identify as JSON, try ' +
                '<a href="http://bibsoup.net/upload">uploading it to bibsoup first</a>, then use the collection address here.' +
                ' Also, note that there is currently a size limitation for querying a file on a different domain...)</p>' +
                '<form action="" method="GET">' +
                '<p>Web address of file: <input type="text" name="source" id="source" /> (for example, try ' +
                '<a href="?source=http://bibsoup.net/test/pitman.json">http://bibsoup.net/test/pitman.json</a>)</p>' +
                '<p>or write / paste JSON in here:</p>' +
                '<p><textarea name="data" id="data"></textarea></p>' +
                '<p><input type="submit" name="submit" value="submit" id="submit" class="btn primary" /></p>' +
                '</form></div>';
            $('#jtedit').append(fromuser);
            $('#data').css({"width":"300px","height":"200px"});
        }
        
        // ===============================================
        // setup up the jtedit screen
        var jtedit_setup = function(obj) {
            // append the jtedit div, put the editor, the menus and the raw JSON in it
            $('#jtedit',obj).remove();
            $(obj).append('<div id="jtedit" class="clearfix"></div>');
            $('#jtedit').append(jtedit_menu_content);
            $('.jtedit_field_opts').hide();
            $('#jtedit_menu').hide();
            $('#jtedit').append('<textarea id="jtedit_json">' + JSON.stringify(parsetable(),"","    ") + '</textarea>');
            $('#jtedit_json').hide();
        }
        
        // apply binding to jtedit parts
        var jtedit_bindings = function() {
            $('.jtedit').autoResize({"minWidth": 60,"maxWidth": 500,"minHeight": 20,"maxHeight": 200,"extraSpace": 10});
            $('.jtedit').bind('blur',updates);
            $('.jtedit_key').bind('focus',opts).bind('mouseup',selectallg);
            $('.jtedit_field').bind('focus',opts).bind('mouseup',selectallg);
            $('#jtedit_json').bind('focus',selectall).bind('mouseup',selectallg);
            $('.jtedit_json').bind('click',jtedit_json);
            $('.jtedit_delete').bind('click',jtedit_delete);
            $('.jtedit_minimise').bind('click',jtedit_minimise);
            $('.jtedit_minall').bind('click',jtedit_minall);
            $('.jtedit_maxall').bind('click',jtedit_maxall);
            $('.jtedit_addrow').bind('click',jtedit_addrow);
            $('.jtedit_list').bind('click',jtedit_list);
            $('.jtedit_save').bind('click',jtedit_save);
            $('.jtedit_object').bind('click',jtedit_object);
            $('.jtedit_nomenu').bind('click',jtedit_nomenu);
            $('.jtedit_help').bind('click',jtedit_help);
        }


        // ===============================================
        // create the plugin on the page
        return this.each(function() {

            obj = $(this);
            jtedit_setup(obj);
            
            if (!options.data) {
                if (options.source) {
                    data_from_source(options.source);
                } else {
                    data_from_user();
                }
            } else {
                $('#jtedit').prepend(tablify(options.data,options.edit));
                jtedit_bindings();
                $('#jtedit_json').val(JSON.stringify(parsetable(),"","    "));
            }
        });

    }
})(jQuery);


var jtedit_menu_content = '<div id="jtedit_menu">' +
    '<div  class="jtedit_nomenu"><a href=""> X </a></div>' +
    '<div  class="jtedit_buttons">' +
    '<p><strong>Row options</strong></p>' +
    '<a class="jtedit_minimise btn small span2" href="">minimise / show</a><br />' +
    '<a class="jtedit_addrow btn small span2" href="">add row after</a><br />' +
    '<a class="jtedit_delete btn small danger span2" href="">delete row</a><br />' +
    '<span class="jtedit_field_opts">' +
    '<p><strong>Field options</strong></p>' +
    '<a class="jtedit_list btn small span2" href="">make a list</a><br />' +
    '<a class="jtedit_object btn small span2" href="">make an object</a><br />' +
    '</span>' +
    '<p><strong>General options</strong></p>' +
    '<a class="jtedit_json btn small span2" href="">show JSON</a><br />' +
    '<a class="jtedit_minall btn small span2" href="">minimise all</a><br />' +
    '<a class="jtedit_maxall btn small span2" href="">show all</a><br />' +
    '<a class="jtedit_help btn info small span2" href="">HELP !</a><br />' +
    //'<a class="jtedit_save btn small success span2" href="">save changes</a><br />' +
    '</div></div>';



var jtedit_help_content = '<div id="jtedit_help">' +
    '<p>jtedit is a tool for editing JSON - just click on any of the text to edit the content. Note that from the options bar ' +
    ' you can hide a row (just for the sake of viewing your data easier), delete a row, add a new row, or change a value to a list or object.</p>' +
    '<p>Strings have no border. Lists have a solid left border. Objects have a dotted left border.</p>' +
    '<h4>About jtedit</h4>' +
    '<p>JSON objects are displayed in a table-like format. <br /><strong>Lists</strong> are identified by a <strong>solid black left border</strong>' +
    '<br /><strong>Objects</strong> are identified by a <strong>dotted black left border</strong>.' +
    '<br />Click on anything to edit and view options. (If uneditable, text will be faded)</p>' +
    '<h4>About JSON</h4>' +
    '<p>JSON is a simple language for writing collections of records.</p>' +
    '<p>JSON can include <strong>strings</strong>, <strong>lists</strong>, <strong>objects</strong>, and <strong>keys</strong> that point to them.</p>' +
    '<p>Below are some examples.</p>' +
    '<h4>A shopping list</h4>' +
    '<p>Shopping lists are just lists of strings - e.g. things that we want to buy.</p>' +
    '<ul><li>Milk</li><li>Juice</li><li>tin of beans</li></ul>' + 
    '<p>in JSON, this would just be a JSON list of strings:</p>' +
    '<p>[<br />&nbsp;&nbsp;&nbsp;&nbsp;"Milk",<br />&nbsp;&nbsp;&nbsp;&nbsp;"Juice",<br />&nbsp;&nbsp;&nbsp;&nbsp;"tin of beans"<br />]</p>' +
    '<p>So a JSON list is surrounded by <strong>[</strong> and <strong>]</strong>, and each value is enclosed in <strong>"</strong> quotes' +
    ' and the values are separated by commas.</p>' +
    '<p>A JSON object is similar, except that it has keys pointing to the values. Here is an example:</p>' +
    '<h4>A business card</h4>' +
    '<p>Business cards are just a collection of strings that have keys explaining what they are.</p>' +
    '<ul><li>Name: Mark</li><li>Position: Chief</li><li>Website: www.mygreatsite.com</li></ul>' + 
    '<p>in JSON, this would be a JSON object:</p>' +
    '<p>{<br />&nbsp;&nbsp;&nbsp;&nbsp;"Name": "Mark",<br />&nbsp;&nbsp;&nbsp;&nbsp;"Position": "Chief",<br />' +
    '&nbsp;&nbsp;&nbsp;&nbsp;"Website": "www.mygreatsite.com"<br />}</p>' +
    '<p>So a JSON object is enclosed in <strong>{</strong> and <strong>}</strong> curly brackets, it has keys in quotes, and they are separated from their ' +
    'values by <strong>:</strong> colons (and the values are enclosed in quotes, too).' +
    '<h4>Putting them together</h4>' +
    '<p>In the list example, strings are separated by commas; in the object example, strings are pointed at by keys. But keys can also point to lists, and' +
    'lists can also be lists of objects, or lists of other lists. Here is a combined example:</p>' +
    '<h4>Business cards with shopping lists, for two people</h4>' +
    '<p>[<br />&nbsp;&nbsp;&nbsp;&nbsp;{<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Name": "Mark",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Position": "Chief",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Website": "www.mygreatsite.com",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"shopping_list": [<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Milk",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Juice",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"tin of beans"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;]<br />&nbsp;&nbsp;&nbsp;&nbsp;},' +
    '<br />&nbsp;&nbsp;&nbsp;&nbsp;{<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Name": "Peter",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Position": "Chief Too",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Website": "www.hisgreatsite.com",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"shopping_list": [<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Cheese",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Juice",<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"open data"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;]<br />&nbsp;&nbsp;&nbsp;&nbsp;}<br />]</p>' +
    '<a href="" class="jtedit_nohelp btn info">close</a>' +
    '</div>';


var jtedit_schema_example = {
    "description":"a bibjson dataset collection schema",
    "type":"object",
    "properties":{
        "metadata":{
            "description":"collection metadata",
            "required":true,
            "type":"object",
            "properties":{
                "id":{
                    "description":"a unique collection identifier",
                    "type":"string",
                    "required":true
                },
                "title":{
                    "description":"a human friendly collection name, suitable as html title element",
                    "type":"string",
                    "required":true
                },
                
                "created":{ 
                            "type":"string",
                            "format": "date-time" },     
                "modified":{ "type":"string",
                              "format": "date-time" },
                "source":{
                    "description":"The URL where the collection file was uploaded from",
                    "type":"string",
                    "format": "url"
                },
                "owner":{
                    "description":"the username of the collection owner",
                    "type":"string"
                },
                "query":{
                    "description":"the query used to build this particular collection, if any",
                    "type":"string"
                },
                "from":{
                    "description":"the starting record if currently showing a subset",
                    "type":"number"
                },
                "size":{
                    "description":"number of records in current display, e.g. if a subset",
                    "type":"number"
                },
                "namespaces":{
                    "description":"namespaces used in this collection",
                    "type":"object",
                    "properties":{
                        "ns1":{
                            "description":"a namespace URL",
                            "type":"string",
                            "format":"url"
                        }
                    }
                }
            }
        },
        "records":{
            "description":"a list of records",
            "type": "array",
            "required":true,
            "items":{
                "description":"a record object",
                "type":"object",
                "properties":{
                    "collections":{
                        "description":"list of collections this record belongs to",
                        "type":"array",
                        "items":{ "type":"string" }
                    },
                    "authors":{
                        "description":"list of author name strings relevant to this record",
                        "type":"array",
                        "items":{ "type":"string" }
                    },
                    "editors":{
                        "description":"list of editor name strings relevant to this record",
                        "type":"array",
                        "items":{ "type":"string" }
                    },
                    "links":{
                        "description":"list of link objects relevant to this record",
                        "type":"array",
                        "items":{ 
                            "type":"object",
                            "properties":{
                                "url":{ "type":"string" },
                                "required":true,
                                "anchor":{
                                    "description":"text to display inside link",
                                    "type":"string"
                                }
                            }
                        }
                    },
                    "ids":{
                        "description":"list of unique identifiers for this record.",
                        "type":"array",
                        "items":{ 
                            "type":"object",
                            "properties":{
                                "namespace":{ "type":"string" },
                                "required":true,
                                "id":{
                                    "description":"the identifier",
                                    "type":"string",
                                    "required":true
                                }
                            }
                        }
                    },
                    "title":{ "type":"string" },
                    "booktitle":{ "type":"string" },
                    "chapter":{ "type":"string" },
                    "edition":{ "type":"string" },
                    "institution":{ "type":"string" },
                    "journal":{ "type":"string" },
                    "number":{ "type":"string" },
                    "organization":{ "type":"string" },
                    "series":{ "type":"string" },
                    "school":{ "type":"string" },
                    "publisher":{ "type":"string" },
                    "pages":{ "type":"string" },
                    "volume":{ "type":"string" },
                    "year":{ "type":"string" },
                    "month":{ "type":"string" },
                    "day":{ "type":"string" },
                    "type":{
                        "type":"string",
                        "description": "Bibliographic type, with list of acceptable values. Required and optional elements depend on type"
                    },
                    "howpublished":{ 
                        "type":"string",
                        "description": "adapted from BibTeX type misc, but also useful for other biblio types if more finely structured information is not available." 
                    }  
                }
            }
        }
    }
}

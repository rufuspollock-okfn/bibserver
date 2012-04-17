/*
 * jquery.jtedit.js
 *
 * a tool for prettily displaying JSON objects
 * and allowing edit of them
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2012. http://copyheart.org
 * Copying is an act of love. Please copy and share.
 *
 * If you need more licensyness, the most you are going to get from me is
 * http://sam.zoy.org/wtfpl/COPYING
 *
 */


(function($){
    $.fn.jtedit = function(options) {

        // specify the defaults
        var defaults = {
            "editable":true,                // whether or not to make the table editable
            "source":undefined,             // a source from which to GET the JSON data object
            "target":undefined,             // a target to which updated JSON should be POSTed
            "noedit":[],                    // a list of keys that should not be editable, when edit is enabled
            "hide":[],                      // a list of keys that should be hidden from view
            "data":undefined,               // a JSON object to render for editing
            "delete_redirect":"#",          // where to redirect to after deleting
            "addable":[],                   // things that should be provided as addables to the item
            "tags": []
        }

        // add in any overrides from the call
        var options = $.extend(defaults,options)

        // add in any options from the query URL
        var geturlparams = function() {
            var vars = [], hash
            var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&')
            for (var i = 0; i < hashes.length; i++) {
                    hash = hashes[i].split('=')
                    vars.push(hash[0])
                    if (!(hash[1] == undefined)) {
                        hash[1] = unescape(hash[1])
                        if (hash[0] == "source") {
                            hash[1] = hash[1].replace(/"/g,'')
                        } else if (hash[0] == "data") {
                            hash[1] = $.parseJSON(hash[1])
                        }
                    }
                    vars[hash[0]] = hash[1]
            }
            return vars
        }
        $.extend(options,geturlparams())


        // ===============================================

        // create a pretty display of a JSON record
        var visify = function(data,edit) {
            edit == undefined ? edit = options.editable : ""
            data == undefined ? data = options.data : ""
            var isdict = false
            data.constructor.toString().indexOf("Array") == -1 ? isdict = true : ""
            var s = ""
            for (var key in data) {
                var partisdict = false
                data[key].constructor.toString().indexOf("Array") == -1 ? partisdict = true : ""
                $.inArray(key,options.noedit) != -1 ? editable = false : editable = edit
                s += '<div class="jtedit_kvcontainer clearfix'
                $.inArray(key,options.hide) != -1 ? s += ' jtedit_hidden' : ""
                s += '">'
                
                // do keys
                s += '<div class="jtedit_optionsgroup btn-group">'
                s += '<a class="dropdown-toggle" data-toggle="dropdown" href="#"><i class="icon-cog"></i></a>'
                s += '<ul class="dropdown-menu">'
                if (editable) {
                    isdict ? addname = key : addname = ""
                    !partisdict ? s += '<li><a class="jtedit_addanother" href=""><i class="icon-plus"></i> add another ' + addname + '</a></li>' : ""
                    if (addname.substr(-1) == "y") {
                        addname = addname.substr(0,-1) + "ies"
                    } else {
                        if (addname.length > 0 && !partisdict) {
                            addname = addname + "s"
                        } else {
                            addname = "this"
                        }
                    }
                    s += '<li><a class="jtedit_remove" href="#"><i class="icon-remove"></i> Remove ' + addname + '</a></li>'
                    partisdict ? s += '<li><a class="jtedit_tolist" href="#"><i class="icon-edit"></i> Make this a list</a></li>' : ""
                    //s += '<li><a class="jtedit_showhidedetails" href="#"><i class="icon-minus"></i> Hide details</a></li>'
                }                
                s += '</ul></div>'
                if (isdict) {
                    key.length > 30 ? s += '<textarea class="jtedit_key"' : s += '<input type="text" class="jtedit_key"'
                    !editable ? s += ' disabled="disabled" ' : false
                    key.length > 30 ? s += '>' + key + '</textarea>' : s += ' value="' + key + '" />'
                }
                
                // do values
                s += '<div class="jtedit_vals">'
                if (typeof(data[key]) == 'object') {
                    s += visify(data[key],editable)
                } else {
                    data[key].length > 30 ? s += '<textarea class="jtedit_value"' : s += '<input type="text" class="jtedit_value"'
                    !editable ? s += ' disabled="disabled" ' : ""
                    data[key].length > 30 ? s += '>' + data[key] + '</textarea>' : s += ' value="' + data[key] + '" />'
                }
                
                s += '</div>' // close the listitems
                s += '</div>' // close the kv container
            }
            return s
        }
        
        // meta stuff for visify. call this usuall
        var dovisify = function(data) {
            $('#jtedit_visual').html( visify( data ) )
            $('.jtedit_key, .jtedit_value').autoResize({minHeight: 20, maxHeight:300, minWidth:50, maxWidth: 250, extraSpace: 5})
            $('.jtedit_key, .jtedit_value').bind('blur',updates)
            $('.jtedit_key, .jtedit_value').bind('mouseup',selectall)
            $('.jtedit_key').autocomplete({source:options.tags})
            $('.jtedit_remove').bind('click',jtedit_remove)
            $('.jtedit_showhidedetails').bind('click',jtedit_showhidedetails)
            $('.jtedit_tolist').bind('click',jtedit_tolist)
            $('.jtedit_optionsgroup').bind('mouseenter',jtedit_optionswarn)
            $('.jtedit_optionsgroup').bind('mouseleave',jtedit_optionswarnout)
            $('.jtedit_addanother').bind('click',jtedit_addanother)
        }

        // parse visualised JSON
        var parsevis = function(visarea) {
            if (visarea == undefined) {
                var visarea = $('#jtedit_visual')
            }
            if (visarea.children('.jtedit_kvcontainer').first().children('.jtedit_key').length) {
                var json = {}
            } else {
                var json = []
            }
            visarea.children('.jtedit_kvcontainer').each(function() {
                var val = ""
                if ($(this).children('.jtedit_vals').children('.jtedit_kvcontainer').length > 0) {
                    val = parsevis($(this).children('.jtedit_vals'))
                } else {
                    val = $(this).children('.jtedit_vals').children('.jtedit_value').val()
                }
                if ($(this).children('.jtedit_key').length) {
                    json[$(this).children('.jtedit_key').val()] = val
                } else {
                    if (val != undefined) {
                        if (val.length > 0 || typeof(val) == 'object') {
                            json.push(val)
                        }
                    }
                }
            })
            return json
        }
        
        // ===============================================
        
        // update JSON when changes occur on visual display
        var updates = function(event) {
            $('#jtedit_json').val(JSON.stringify(parsevis(),"","    "))
            /*$(this).removeClass('text_empty')
            if ($(this).val() == "") {
                $(this).addClass('text_empty')
            }*/
        }

        // select all in input / textarea
        var selectall = function(event) {
            event.preventDefault()
            $(this).select()
        }

        // save the record
        var jtedit_saveit = function(event,datain) {
            event.preventDefault()
            !datain ? datain = $.parseJSON(jQuery('#jtedit_json').val()) : false
            !options.target ? options.target = prompt('Please provide URL to save this record to:') : false
            if (options.target) {
                $.ajax({
                    url: options.target
                    , type: 'POST'
                    , data: JSON.stringify(datain)
                    , contentType: "application/json; charset=utf-8" 
                    , dataType: 'json'
                    , processData: false
                    , success: function(data, statusText, xhr) {
                        alert("Changes saved")
                        window.location = window.location
                    }
                    , error: function(xhr, message, error) {
                        alert("Error... " + error)
                    }
                })
            } else {
                alert('No suitable URL to save to was provided')
            }
        }

        // delete the record
        var jtedit_deleteit = function(event) {
            event.preventDefault()
            if (!options.target) {
                alert('There is no available source URL to delete from')
            } else {
                var confirmed = confirm("You are about to irrevocably delete this. Are you sure you want to do so?")
                if (confirmed) {
                    $.ajax({
                        url: options.target
                        , type: 'DELETE'
                        , success: function(data, statusText, xhr) {
                            alert("Deleted.")
                            window.location = options.delete_redirect
                        }
                        , error: function(xhr, message, error) {
                            alert("Error... " + error)
                        }
                    })
                }
            }
        }
        
        // switch visual type
        var jtedit_mode = function(event) {
            event.preventDefault()
            if ( $('#jtedit_json').is(':visible') ) {
                $(this).html('view as JSON')
                $('#jtedit_json').hide()
                dovisify( $.parseJSON( $('#jtedit_json').val() ) )
                $('#jtedit_visual').show()
            } else {
                $(this).html('view tabular')
                $('#jtedit_visual').hide()
                $('#jtedit_json').val( JSON.stringify(parsevis(),"","    ") )
                $('#jtedit_json').show()
            }
        }
        
        // remove part from object
        var jtedit_remove = function(event) {
            event.preventDefault()
            $(this).closest('.jtedit_kvcontainer').remove()
            updates(event)
        }
        
        // highlight an object on options hover
        var jtedit_optionswarn = function(event) {
            event.preventDefault()
            $(this).css({'color':'red'})
            $(this).parent().addClass('jtedit_optionswarn')
        }
        var jtedit_optionswarnout = function(event) {
            event.preventDefault()
            $(this).css({'color':'#000'})
            $(this).parent().removeClass('jtedit_optionswarn')
        }
        
        // add another item to a list
        var jtedit_addanother = function(event) {
            event.preventDefault()
            alert("add another")
        }
        
        // add an item to the object
        var jtedit_additem = function(event) {
            event.preventDefault()
            alert("add a new item to this object")
        }
        
        // convert to a list
        var jtedit_tolist = function(event) {
            event.preventDefault()
            alert("convert to list")
        }
        
        // show or hide details of an object
        var jtedit_showhidedetails = function(event) {
            event.preventDefault()
            if ($(this).hasClass('jtedit_beenhidden')) {
                $(this).removeClass('jtedit_beenhidden')
                $(this).html('<i class="icon-minus"></i> Hide details')
                $(this).closest('.jtedit_kvcontainer').children('.jtedit_vals').show()
                $(this).closest('.jtedit_kvcontainer').children('.jtedit_hidnote').remove()
            } else {
                $(this).addClass('jtedit_beenhidden')
                $(this).html('<i class="icon-plus"></i> Show details')
                $(this).closest('.jtedit_kvcontainer').children('.jtedit_vals').hide()
                $(this).closest('.jtedit_kvcontainer').children('.jtedit_optionsgroup').after('<span class="jtedit_hidnote"><strong>. . .</strong></span>')
            }
        }
        
        // ===============================================

        // get data from a source URL
        var data_from_source = function(sourceurl) {
            $.ajax({
                url: sourceurl
                , type: 'GET'
                , success: function(data, statusText, xhr) {
                    options.data = data
                    dovisify()
                    $('#jtedit_json').val(JSON.stringify(parsevis(),"","    "))
                }
                , error: function(xhr, message, error) {
                    options.source = false
                    alert("Sorry. Your data could not be parsed from " + sourceurl + ". Please try again, or paste your data into the provided field.")
                    $('#jtedit_visual').hide()
                    $('#jtedit_json').show()
                }
            })
        }

        // setup up the jtedit screen
        var jtedit_setup = function(obj) {
            $('#jtedit',obj).remove()
            $(obj).append('<div id="jtedit" class="clearfix"></div>')
            var actions = '<div class="jtedit_actions"><div class="btn-group">' +
                '<a class="btn dropdown-toggle" data-toggle="dropdown" href="#"><i class="icon-cog"></i> options </a>' +
                '<ul class="dropdown-menu">' +
                '<li><a class="jtedit_mode" href="">view as JSON</a></li>'
            actions += '<li><a class="jtedit_additem" href="">add a new item to this</a></li>'
            actions += '</ul></div>'
            if ( options.editable ) {
                actions += '<a class="jtedit_saveit btn btn-primary" href="save"><i class="icon-check icon-white"></i> save</a> ' + 
                '<a class="btn btn-warning" href=""><i class="icon-refresh icon-white"></i> reload</a> ' + 
                '<a class="jtedit_deleteit btn btn-danger" href=""><i class="icon-remove icon-white"></i> delete</a>'
            }
            actions += '</div>'
            $('#jtedit').append(actions + '<div id="jtedit_visual"></div><textarea id="jtedit_json"></textarea>') // + actions)
            
            var testdata = '{"abstract": "Folien zu einem Vortrag auf der ODOK 2010 in Leoben zu Linked Data und Open Data, mit einer knappen Darstellung der Linked-Open-Data-Aktivit\u110e\u1162ten im hbz-Verbund.", "added-at": "2011-02-17T13:00:20.000+0100", "author": ["pretend",["list","inalist"],{"id": "PohlAdrian","name": "Pohl, Adrian"},{"id": "PohlAdrian","name": "Pohl, Adrian"}], "journal":{"id":"somejournal","name":"somename"}, "biburl": "http://www.bibsonomy.org/bibtex/229ff5da471fd9d2706f2fd08c17b43dc/acka47", "cid": "Pohl_2010_LOD", "collection": "pohl", "copyright": "http://creativecommons.org/licenses/by/2.5/", "howpublished": "published via slideshare.net", "id": "531e7aa806574787897314010f29d4cf", "interhash": "558af6397a6aad826d47925a12eda76c", "intrahash": "29ff5da471fd9d2706f2fd08c17b43dc", "keyword": ["ODOK hbz libraries linkeddata myown opendata presentation"], "link": [{"url": "http://www.slideshare.net/acka47/pohl-20100923-odoklod"}], "month": "September", "owner": "test", "timestamp": "2011-02-17T13:00:20.000+0100", "title": "Freie Katalogdaten und Linked Data", "type": "misc", "url": "http://localhost:5000/test/pohl/Pohl_2010_LOD", "year": "2010" }'
            
            if (!options.source && !options.data) {
                $('#jtedit_json').val( testdata )
                $('#jtedit_visual').hide()
            } else {
                $('#jtedit_json').val( JSON.stringify(parsevis(),"","    ") )
                $('#jtedit_json').hide()
            }
            jtedit_bindings()
        }
        
        // apply binding to jtedit parts
        var jtedit_bindings = function() {
            $('.jtedit_saveit').bind('click',jtedit_saveit)
            $('.jtedit_deleteit').bind('click',jtedit_deleteit)
            $('.jtedit_mode').bind('click',jtedit_mode)
            $('.jtedit_additem').bind('click',jtedit_additem)
            /*$('.jtedit_field').each(function() {
                if ( $(this).prev('input').hasClass('jtedit_key') ) {
                    if ( $(this).prev('input').val().search("_date") != -1 ) {
                        $(this).datetimepicker({ dateFormat: 'yy-mm-dd' })
                    }
                }
            })*/

        }


        // ===============================================

        // create the plugin on the page
        return this.each(function() {

            obj = $(this)
            jtedit_setup(obj)
            
            if (options.source) {
                data_from_source(options.source)
            } else if (options.data) {
                dovisify()
                $('#jtedit_json').val(JSON.stringify(parsevis(),"","    "))
            }

        })

    }
})(jQuery)





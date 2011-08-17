jQuery(document).ready(function() {
% for facet in c['config'].display_facet_order:
        $("#fh_${facet}").toggle(function(){ $("#fr_${facet}").show('slow');},function(){$("#fr_${facet}").hide('fast');});
% endfor
    });
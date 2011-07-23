% if c['results'].get_selected_range_end(facet) != -1:

    <em>
    ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}
    % if c['config'].display_upper(facet, str(c['results'].get_selected_range_start(facet)), str(c['results'].get_selected_range_end(facet))):
        - 
        ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_end(facet)))}
    % endif

    (${c['results'].numFound()})
    </em>
    &nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a>

% else:

    <em>${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}+
    (${c['results'].numFound()})
    </em>&nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a>
    
% endif
<br/>
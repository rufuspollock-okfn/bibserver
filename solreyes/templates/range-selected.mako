% if c['results'].get_selected_range_end(facet) != -1:
    <em>
        ${c['results'].get_selected_range_start(facet)} - ${c['results'].get_selected_range_end(facet)}
        (${c['results'].numFound()})
    </em>
    &nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a>
% else:
    <em>
    ${c['results'].get_selected_range_start(facet)}+
    (${c['results'].numFound()})
    </em>
    &nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a>
% endif
<br/>
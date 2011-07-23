% for value, count in c['results'].get_ordered_facets(facet):
    % if not c['results'].in_args(facet, value):
        <a href="${c['url_manager'].get_add_url(facet, value)}">
        ${c['config'].get_value_display(facet, value)} (${count})
        </a><br/>
    % endif
% endfor
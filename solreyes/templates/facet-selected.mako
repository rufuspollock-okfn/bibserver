% for value, count in c['results'].get_ordered_facets(facet):
    % if c['results'].in_args(facet, value):
        <em>
        ${c['config'].get_value_display(facet, value)} (${count})
        </em>&nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet, value)}">x</a>
        <br/>
    % endif
% endfor
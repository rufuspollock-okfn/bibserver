% for lower, upper, count in c['results'].get_ordered_facets(facet):
    <a href="${c['url_manager'].get_add_url(facet, lower, upper)}">
    % if upper != -1:
        ${lower} - ${upper} (${count})
    % else:
        ${lower}+ (${count})
    % endif
    </a><br/>
% endfor
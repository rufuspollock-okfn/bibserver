% for lower, upper, count in c['results'].get_ordered_facets(facet):
    <a href="${c['url_manager'].get_add_date_url(facet, lower, upper)}">
    % if upper != -1:
        ${c['config'].get_value_display(facet, str(lower))}
        % if c['config'].display_upper(facet, str(lower), str(upper)):
            - 
            ${c['config'].get_value_display(facet, str(upper))} 
        % endif
        (${count})
    % else:
        ${c['config'].get_value_display(facet, str(lower))}+ (${count})
    % endif
    </a><br/>
% endfor
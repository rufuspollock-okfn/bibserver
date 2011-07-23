% for facet in c['config'].display_facet_order:
    % if c['results'].has_values(facet):
        <a href="" id="fh_${facet}"><strong>${c['config'].get_facet_display(facet)}</strong></a><br/>
        <div id="selected_${facet}">
        
        % if facet in c['config'].facet_ranges.keys():
        
            % if c['results'].in_args(facet):
                % if c['results'].get_selected_range_end(facet) != -1:
                    <em>${c['results'].get_selected_range_start(facet)} - ${c['results'].get_selected_range_end(facet)}
                    (${c['results'].numFound()})
                    </em>&nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a><br/>
                % else:
                    <em>${c['results'].get_selected_range_start(facet)}+
                    (${c['results'].numFound()})
                    </em>&nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a><br/>
                % endif
            % endif
            
        % elif facet in c['config'].facet_dates.keys():
            % if c['results'].in_args(facet):
                % if c['results'].get_selected_range_end(facet) != -1:
                    <em>
                    ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}
                    % if c['config'].display_upper(facet, str(c['results'].get_selected_range_start(facet)), str(c['results'].get_selected_range_end(facet))):
                        - 
                        ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_end(facet)))}
                % endif
                (${c['results'].numFound()})
                </em>
                &nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a><br/>
                % else:
                    <em>${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}+
                    (${c['results'].numFound()})
                    </em>&nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a><br/>
                % endif
            % endif 
    
        % else:
        
            % for value, count in c['results'].get_ordered_facets(facet):
                % if c['results'].in_args(facet, value):
                    <em>
                    ${c['config'].get_value_display(facet, value)} (${count})
                    </em>&nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet, value)}">x</a>
                    <br/>
                % endif
            % endfor
            
        % endif
        </div>
        
        
    % if c['results'].has_values(facet):
        <div id="fr_${facet}" style="display:none">
        % if facet in c['config'].facet_ranges.keys():
            % if not c['results'].in_args(facet):
                % for lower, upper, count in c['results'].get_ordered_facets(facet):
                    <a href="${c['url_manager'].get_add_url(facet, lower, upper)}">
                    % if upper != -1:
                        ${lower} - ${upper} (${count})
                    % else:
                        ${lower}+ (${count})
                    % endif
                    </a><br/>
                % endfor
            % endif
        % elif facet in c['config'].facet_dates.keys():
            % if not c['results'].in_args(facet):
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
            % endif
        % else:
            % for value, count in c['results'].get_ordered_facets(facet):
                % if not c['results'].in_args(facet, value):
                    <a href="${c['url_manager'].get_add_url(facet, value)}">
                    ${c['config'].get_value_display(facet, value)} (${count})
                    </a><br/>
                % endif
            % endfor
        % endif
        </div><br/>
        
    % endif
    % endif
% endfor
<div class="search_constraints">
% for facet, values in c['results'].get_search_constraints().iteritems():
   
   % if facet not in c['implicit_facets']:
   
        % if facet in c['config'].facet_ranges.keys():
            <div class="search_constraint">
                ${c['config'].get_facet_display(facet)} : 
        
                % if c['results'].get_selected_range_end(facet) != -1:
                    ${c['results'].get_selected_range_start(facet)} - ${c['results'].get_selected_range_end(facet)}
                % else:
                    <em>${c['results'].get_selected_range_start(facet)}+
                % endif
                &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet)}">x</a>
            </div>
                
        % elif facet in c['config'].facet_dates.keys():
            <div class="search_constraint">
                ${c['config'].get_facet_display(facet)} : 
                % if c['results'].get_selected_range_end(facet) != -1:
                    ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}
                    % if c['config'].display_upper(facet, str(c['results'].get_selected_range_start(facet)), str(c['results'].get_selected_range_end(facet))):
                        - 
                        ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_end(facet)))}
                    % endif
                % else:
                    ${c['config'].get_value_display(facet, str(c['results'].get_selected_range_start(facet)))}+
                % endif
                &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet)}">x</a>
            </div>
    
        % else:
            % for value in values:
                <div class="search_constraint">
                    ${c['config'].get_facet_display(facet)} : 
                    ${c['config'].get_value_display(facet, value)}
                    &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet, value)}">x</a>
                </div>
            % endfor
        % endif
    
    % endif
% endfor
</div>


    
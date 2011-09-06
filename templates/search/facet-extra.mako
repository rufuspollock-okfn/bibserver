% for facet in c['config'].display_facet_order:
    % if c['config'].get_facet_display(facet) not in c['implicit_facets']:
        <div class="facet">
        % if c['results'].has_values(facet):
            <div class="facet_heading">
                <a href="" class="facet_heading" id="fh_${facet}"><span class="facet_pm">+&nbsp;</span>${c['config'].get_facet_display(facet)}</a>
            </div>
            <div id="selected_${facet}" class="facet_value">
                        
            % for value, count in c['results'].get_ordered_facets(facet):
                % if c['results'].in_args(facet, value):
                    <em>
                    ${c['config'].get_value_display(facet, value)} (${count})
                    </em>&nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet, value)}">x</a>
                    <br/>
                % endif
            % endfor
                
            </div>
            
            <div id="fr_${facet}" style="display:none" class="facet_value">

            % for value, count in c['results'].get_ordered_facets(facet):
                % if not c['results'].in_args(facet, value):
                    <a href="${c['url_manager'].get_add_url(facet, value)}">
                    ${c['config'].get_value_display(facet, value)} (${count})
                    </a><br/>
                % endif
            % endfor

            </div>
                
        % else:
            <div class="empty_facet">
                <strong>${c['config'].get_facet_display(facet)}</strong>
            </div>
        % endif
        </div>
    % endif
% endfor

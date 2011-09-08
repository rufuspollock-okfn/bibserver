% for facet in c['io'].get_facet_fields():
    % if facet not in c['implicit_facet']:
        <div class="facet">
        % if c['io'].has_values(facet):
            <div class="facet_heading">
                <a href="" class="facet_heading" id="fh_${facet}"><span class="facet_pm">+&nbsp;</span>${facet}</a>
            </div>
            <div id="selected_${facet}" class="facet_value">
                        
            % for value, count in c['io'].get_ordered_facets(facet):
                % if c['io'].in_args(facet, value):
                    <em>
                    ${value} (${count})
                    </em>
                    &nbsp;<a class="delete_url" href="${c['io'].get_delete_url(facet, value)}">x</a>
                    <br/>
                % endif
            % endfor
                
            </div>
            
            <div id="fr_${facet}" style="display:none" class="facet_value">

            % for value, count in c['io'].get_ordered_facets(facet):
                % if not c['io'].in_args(facet, value):
                    <a href="${c['io'].get_add_url(facet, value)}">
                    ${value} (${count})
                    </a><br/>
                % endif
            % endfor

            </div>
                
        % else:
            <div class="empty_facet">
                <strong>${facet}</strong>
            </div>
        % endif
        </div>
    % endif
% endfor

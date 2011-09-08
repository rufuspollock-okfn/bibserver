% for facet in c['io'].get_facet_fields():
    % if facet not in c['implicit_facet']:
        <div class="facet">

            <div class="facet_heading">
                <a href="" class="facet_heading" id="fh_${facet}"><span class="facet_pm">+&nbsp;</span>${facet}</a>
            </div>
            <div id="selected_${facet}" class="facet_selected">
                        
            % for item in c['io'].facet_fields[facet]:
                % if c['io'].in_args(facet, item["term"]):
                    <em>
                    ${item["term"]} (${item["count"]})
                    </em>
                    &nbsp;<a class="delete_url" href="${c['io'].get_delete_url(facet, item['term'])}">x</a>
                    <br/>
                % endif
            % endfor
                
            </div>
                        
            <ul id="fr_${facet}" class="facet_value">

            % for item in c['io'].facet_fields[facet]:
                % if not c['io'].in_args(facet, item["term"]):
                    <li><a href="${c['io'].get_add_url(facet, item['term'])}">
                    ${item['term']}</a> (<span class="count">${item['count']}</span>)
                    </li>
                % endif
            % endfor

            </li>
                
        </div>
    % endif
% endfor

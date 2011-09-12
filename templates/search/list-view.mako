
<% if c['io'].numFound() == 0:
    return
%>




<div class="list_view">
    % for i in range(len(c['io'].set())):
        <div class="list_result_${'odd' if i % 2 == 0 else 'even'}">
            % for field in c['io'].get_display_fields():
                % if c['io'].get_str(c['io'].set()[i], field) != "":
                    <div class="list_result_field">${c['io'].get_str(c['io'].set()[i], field)}</div>
                % endif
            % endfor

            % if "type" in c['io'].set()[i]:
                % if c['io'].set()[i]["type"] == "collection":
                    % for record in c['io'].set()[i]:
                        <div class="list_result_field">${record} - ${c['io'].get_str(c['io'].set()[i], record)}</div>
                    % endfor
                % endif
            % endif

            <table class="list_result_hidden list_table">
            % for record in c['io'].set()[i]:
                <tr>
                <td>${record}</td><td>${c['io'].get_str(c['io'].set()[i], record)}</td>
                </tr>
            % endfor
            </table>

            <div class="list_result_options list_result_hidden">
                <a class="viewrecord" href="/collection/${c['io'].get_str(c['io'].set()[i], "collection", True)}/${c['io'].get_str(c['io'].set()[i], "citekey")}">View record</a>
            </div>

        </div>
    % endfor
</div>

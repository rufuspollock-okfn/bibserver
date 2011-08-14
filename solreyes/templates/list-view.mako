<% if c['results'].set_size() == 0:
    return
%>

<div class="list_view">
    % for i in range(len(c['results'].set())):
        <div class="list_result_${'odd' if i % 2 == 0 else 'even'}">
            % for field in c['config'].display_field_order:
                % if c['results'].get_str(c['results'].set()[i], field) != "":
                    <div class="list_result_field">${c['results'].get_str(c['results'].set()[i], field)}</div>
                % endif
            % endfor

            <div class="list_result_hidden">
            % for record in c['results'].set()[i]:
                % if record not in c['config'].display_field_order and record not in ["_id","_rev","score"]:
                    <div class="list_result_field">${record} - ${c['results'].get_str(c['results'].set()[i], record)}</div>
                % endif
            % endfor
            </div>
            
        </div>
    % endfor
</div>

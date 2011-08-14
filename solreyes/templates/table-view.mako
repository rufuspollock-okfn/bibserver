<% if c['results'].set_size() == 0:
    return
%>

<table class="data_table" cellspacing="0">
    <tr>
% for field in c['config'].display_field_order:
        <th>
            <strong>${c['config'].get_field_name(field)}</strong>
        </th>
% endfor
    </tr>
% for i in range(len(c['results'].set())):
    <tr class="${'odd' if i % 2 == 0 else 'even'}">
    % for field in c['config'].display_field_order:
        <td>
            ${c['results'].get_str(c['results'].set()[i], field)}
        </td>
    % endfor
    </tr>
% endfor

</table>

<% if c['results'].set_size() == 0:
    return
%>

<table border="1" cellspacing="0">
    <tr>
% for field in c['config'].display_field_order:
        <th>
            <strong>${c['config'].get_field_name(field)}</strong>
        </th>
% endfor
    </tr>
% for result in c['results'].set():
    <tr>
%   for field in c['config'].display_field_order:
        <td>
            ${c['results'].get_str(result, field)}
        </td>
%   endfor
    </tr>
% endfor
</table>

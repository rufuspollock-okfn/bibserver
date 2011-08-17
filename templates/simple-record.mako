% for result in c['results'].set():
    <table>
%   for field in c['config'].display_fields:
        <tr>
            <td>
                <strong>${c['config'].display_field_names[field]}</strong>:
            </td>
            <td>
%        if hasattr(result.get(field), "append"):
            ${", ".join([str(val) for val in result.get(field)])}
%        else:
            ${str(result.get(field))}
%        endif
            </td>
        </tr>
%    endfor
    </table><br/>
% endfor
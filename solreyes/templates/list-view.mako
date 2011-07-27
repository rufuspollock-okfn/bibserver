<% if c['results'].set_size() == 0:
    return
%>

<table>
% for result in c['results'].set():
    <tr>
    <br />
%   for field in c['config'].display_field_order:
%       if c['results'].get_str(result,field) != '':
%           if field == "title":
                <a href="">
%           endif
%           if field == "journal":
                <em>
%           endif
            ${c['results'].get_str(result, field)}<br />
%           if field == "title":
                </a>
%           endif
%           if field == "journal":
                </em>
%           endif
%       endif
%   endfor
    </tr>
% endfor
</table>

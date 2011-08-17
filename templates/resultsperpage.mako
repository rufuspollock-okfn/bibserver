<div class="results_per_page">

    <div class="rpp_label">Show</div>
% for rpp in c['config'].results_per_page_options:
%   if rpp == c['results'].page_size():
    <div class="current_rpp">${rpp}</div>
%   else:
    <div class="potential_rpp"><a href="${c['url_manager'].get_rpp_url(rpp)}">${rpp}</a></div>
%   endif
% endfor

</div>

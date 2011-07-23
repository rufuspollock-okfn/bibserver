<div class="results_per_page">
    Results per page: 
% for rpp in c['config'].results_per_page_options:
%   if rpp == c['results'].page_size():
    <strong>${rpp}</strong>
%   else:
    <a href="${c['url_manager'].get_rpp_url(rpp)}">${rpp}</a>
%   endif
% endfor

</div>
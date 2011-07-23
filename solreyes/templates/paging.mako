<div class="paging">
    <!-- Paging -->
    
%   if not c['results'].is_start():
        <a href="${c['url_manager'].get_position_url(0)}">1 - ${c['results'].first_page_end()}</a>
        ...
%   endif

%       for start, finish in c['results'].get_previous(3):
            <a href="${c['url_manager'].get_position_url(start)}">${start + 1} - ${finish}</a>
%       endfor
            <strong>${c['results'].start_offset(1)} - ${c['results'].finish()}</strong>

%       for start, finish in c['results'].get_next(3):
            <a href="${c['url_manager'].get_position_url(start)}">${start + 1} - ${finish}</a>
%       endfor

%   if not c['results'].is_end():
        ...
        <a href="${c['url_manager'].get_position_url(c['results'].last_page_start())}">
        ${c['results'].last_page_start() + 1} - 
        ${c['results'].numFound()}</a>
%   endif
</div>
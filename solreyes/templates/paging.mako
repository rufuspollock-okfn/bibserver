<div class="paging">

    <div class="paging_label">Results</div>
    
    <!-- Paging -->
    
%   if not c['results'].is_start():
        <div class="potential_page"><a href="${c['url_manager'].get_position_url(0)}">1 - ${c['results'].first_page_end()}</a></div>
        <div class="paging_label">...</div>
%   endif

%       for start, finish in c['results'].get_previous(10):
            <div class="potential_page"><a href="${c['url_manager'].get_position_url(start)}">${start + 1} - ${finish}</a></div>
%       endfor
            <div class="current_page">${c['results'].start_offset(1)} - ${c['results'].finish()}</div>

%       for start, finish in c['results'].get_next(10):
            <div class="potential_page"><a href="${c['url_manager'].get_position_url(start)}">${start + 1} - ${finish}</a></div>
%       endfor

%   if not c['results'].is_end():
        <div class="paging_label">...</div>
        <div class="potential_page"><a href="${c['url_manager'].get_position_url(c['results'].last_page_start())}">
        ${c['results'].last_page_start() + 1} - 
        ${c['results'].numFound()}</a></div>
%   endif
</div>

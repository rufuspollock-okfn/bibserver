<div class="sort_options">
% if len(c['results'].current_sort_fields()) > 0:
    <div class="sort_label">
        Sorting by: 
    </div>
    % for sortby, direction in c['results'].current_sort_order():
        <div class="current_sort_option">
        ${c['config'].sort_fields[sortby].get("display", sortby)}
        % if direction == 'asc':
            (<strong>^</strong> <a href="${c['url_manager'].get_sort_url(sortby, 'desc')}">v</a>)
        % endif
        % if direction == 'desc':
            (<a href="${c['url_manager'].get_sort_url(sortby, 'asc')}">^</a> <strong>v</strong>)
        % endif
        <a class="delete_url" href="${c['url_manager'].get_unsort_url(sortby)}">x</a>
        </div>
        <div class="sort_label">
            then
        </div>
    % endfor
% endif

% if len([f for f in c['config'].sort_fields.keys() if f not in c['results'].current_sort_fields()]) > 0:
    % if len(c['results'].current_sort_fields()) == 0:
        <div class="sort_label">Sort by:</div>
    % endif

    % for sortby in c['config'].sort_fields.keys():
    %   if sortby not in c['results'].current_sort_fields():
        <div class="potential_sort_option">
            ${c['config'].sort_fields[sortby].get("display", sortby)} (<a href="${c['url_manager'].get_sort_url(sortby, 'asc')}">^</a> <a href="${c['url_manager'].get_sort_url(sortby, 'desc')}">v</a>)
        </div>
    %   endif
    % endfor
% endif
</div>
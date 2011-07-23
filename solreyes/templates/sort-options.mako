<div class="sort_options">
% if len(c['results'].current_sort_fields()) > 0:
    Sorting by: 
    % for sortby, direction in c['results'].current_sort_order():
        <strong>
        ${c['config'].sort_fields[sortby].get("display", sortby)}
        % if direction == 'asc':
            (^ <a href="${c['url_manager'].get_sort_url(sortby, 'desc')}">v</a>)
        % endif
        % if direction == 'desc':
            (<a href="${c['url_manager'].get_sort_url(sortby, 'asc')}">^</a> v)
        % endif
        <a href="${c['url_manager'].get_unsort_url(sortby)}">x</a>
        </strong>
        then
    % endfor
    -
% endif

% if len([f for f in c['config'].sort_fields.keys() if f not in c['results'].current_sort_fields()]) > 0:
    % if len(c['results'].current_sort_fields()) == 0:
        Sort by:
    % endif

    % for sortby in c['config'].sort_fields.keys():
    %   if sortby not in c['results'].current_sort_fields():
        ${c['config'].sort_fields[sortby].get("display", sortby)} (<a href="${c['url_manager'].get_sort_url(sortby, 'asc')}">^</a> <a href="${c['url_manager'].get_sort_url(sortby, 'desc')}">v</a>)
    %   endif
    % endfor
% endif
</div>
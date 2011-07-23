<div class="search_constraints">
% for facet, value in c['results'].get_search_constraints().iteritems():
    <div class="search_constraint">
        ${c['config'].get_facet_display(facet)} : ${value}
        &nbsp;&nbsp;<a href="${c['url_manager'].get_delete_url(facet)}">x</a>
    </div>
% endfor
</div>
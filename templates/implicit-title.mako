<div class="implicit_title">
    % for field in c['implicit_facets'].keys():
        <h1>${c['config'].get_facet_display(field)} : ${", ".join([c['config'].get_value_display(field, x) for x in c['implicit_facets'][field]])}</h1>
    % endfor
</div>
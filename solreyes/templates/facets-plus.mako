 <!-- Faceted Navigation -->

% for facet in c['config'].display_facet_order:
    % if c['results'].has_values(facet):
    
        <a href="" id="fh_${facet}"><strong>${c['config'].get_facet_display(facet)}</strong></a><br/>
        <div id="selected_${facet}">
            % if c['config'].is_range(facet) and c['config'].in_args(facet):
                <%include file="/range-selected.mako"/>
            % elif c['config'].is_date_range(facet) and c['config'].in_args(facet):
                <%include file="/date-selected.mako"/>
            % else:
                <%include file="/facet-selected.mako"/>
            % endif
        </div>
        <div id="visible_${facet}">
           xxxx
        </div>
        <div id="fr_${facet}" style="display:none">
            % if c['config'].is_range(facet) and not c['results'].in_args(facet):
                <%include file="/range-facets.mako"/>
            % elif c['config'].is_date_range(facet) and not c['results'].in_args(facet):
                <%include file="/date-facets.mako"/>
            % else:
                <%include file="/facet-fields.mako"/>
            % endif
        </div>
    
    % endif
% endfor
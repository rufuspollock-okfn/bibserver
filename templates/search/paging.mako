<div class="paging">

    % if int(c['results'].start()) >= c['results'].page_size():
    <form method="get" action="">
          % if 'q' in c:
              <input type="hidden" name="q" value="${c['q']}" />
          % endif
    <input type="hidden" name="from" value="${int(c['results'].start()) - c['results'].page_size()}" />
    <input type="hidden" name="size" value="${c['results'].page_size()}" />
    <input type="submit" class="paging_submit_left" name="submit" value="previous" />
    </form>
    % endif

    <form method="get" action="">
          % if 'q' in c:
              <input type="hidden" name="q" value="${c['q']}" />
          % endif
    <select class="small" name="from" id="page_select">

% for i in range(0, ( c['results'].numFound() / c['results'].page_size() ) + 1):
    % if (i * c['results'].page_size()) == int(c['results'].start()):
    <option value="${i * c['results'].page_size()}" selected>
    % else:
    <option value="${i * c['results'].page_size()}">
    % endif
    ${i * c['results'].page_size() + 1} - 
    % if i * c['results'].page_size() + 1 + c['results'].page_size() < c['results'].numFound():
        ${i * c['results'].page_size() + c['results'].page_size()}
    % else:
        ${c['results'].numFound()}
    % endif
    </option>
% endfor
    
    </select>

    <span class="results_total">of ${c['results'].numFound()} results. </span><span>Show </span>

    <select class="small" name="size" id="rpp_select">

    % for rpp in c['config'].results_per_page_options:
    %   if rpp == int(c['results'].page_size()):
        <option selected>${rpp}</option>
    %   else:
        <option value="${rpp}">${rpp}</option>
    %   endif
    % endfor

    </select>

    <input type="submit" name="submit" value="update" id="paging_trigger" />
    </form>


    % if ( int(c['results'].start()) + int(c['results'].page_size()) ) < c['results'].numFound():
    <form method="get" action="">
          % if 'q' in c:
              <input type="hidden" name="q" value="${c['q']}" />
          % endif
    <input type="hidden" name="from" value="${int(c['results'].start()) + int(c['results'].page_size())}" />
    <input type="hidden" name="size" value="${int(c['results'].page_size())}" />
    <input type="submit" class="paging_submit_right" name="submit" value="next" />
    </form>
    % endif

</div>

<div class="spacer"></div>        


<% if c['results'].numFound() == 0:
    return
%>

<div class="list_view">
    % for i in range(len(c['results'].set())):
        <div class="list_result_${'odd' if i % 2 == 0 else 'even'}">
            % for field in c['config'].display_fields:
                % if c['results'].get_str(c['results'].set()[i], field) != "":
                    <div class="list_result_field">${c['results'].get_str(c['results'].set()[i], field)}</div>
                % endif
            % endfor

            <div class="list_result_hidden">
            % for record in c['results'].set()[i]:
                % if record not in c['config'].display_fields:
                    <div class="list_result_field">${record} - ${c['results'].get_str(c['results'].set()[i], record)}</div>
                % endif
            % endfor
            </div>

        <div class="list_result_options list_result_hidden">
            <a href="/collection/${c['results'].get_str(c['results'].set()[i], "collection", True)}/${c['results'].get_str(c['results'].set()[i], "citekey")}">View record</a> or search 
            <form action="/redirect" method="get">
            <select name="target">
                <option value="http://www.google.com/search?q=">Google</option>
                <option value="http://scholar.google.com/scholar?q=">Google scholar</option>
                <option value="http://www.google.com/search?tbm=bks&q=">Google books</option>
                <option value="http://www.google.com/search?tbm=vid&q=">Google video</option>
                <option value="http://www.google.com/search?tbm=isch&q=">Google images</option>
                <option value="http://www.google.com/search?tbm=blg&q=">Google blogs</option>
                <option value="http://www.google.com/search?q=pitman+site%3Awww.researcherid.com">Google + ResearcherID</option>
                <option value="http://www.google.com/search?q=XXXX+ACM+author+profile+site%3Adl.acm.org">Google + ACM Author Profiles</option>
                <option value="http://www.google.com/search?q=XXXX+site%3Agenealogy.math.ndsu.nodak.edu">Google + Mathemtatics genealogy</option>
                <option value="http://academic.research.microsoft.com/Search?query=">Microsoft academic search</option>
                <option value="http://www.bing.com/search?q=">Bing</option>
                <option value="http://www.bing.com/images/search?q=">Bing images</option>
                <option value="http://www.bing.com/search?q=XXXX+author">Bing + author</option>
                <option value="http://www.bing.com/search?q=XXXX+site%3Aresearcherid.com">Bing + ResearcherID</option>
                <option value="http://thelma.ist.psu.edu/search.php?q=">Homepage Seer</option>
                <option value="http://www.zentralblatt-math.org/zmath/en/search/?q=">Zentralblatt Math</option>
                <option value="http://www.zentralblatt-math.org/zmath/en/authors/?au=">Zentralblatt Math authors</option>
                <option value="http://www.ams.org/mathscinet-mref?dataType=mathscinet&ref=">MathSciNet HTML</option>
                <option value="http://www.ams.org/mathscinet-mref?mref-submit=Search&dataType=bibtex&ref=">MathSciNet BibTex</option>    
            </select>
             for 
            <select name="value">
            % for record in c['results'].set()[i]:
                % if record not in ["_rev","_id","score","collection"]:
                    <option>${c['results'].get_str(c['results'].set()[i], record)}</option>
                % endif
            % endfor
            </select>
            <input type="submit" name="submit" value="go" />
            </form>
        </div>


        </div>
    % endfor
</div>

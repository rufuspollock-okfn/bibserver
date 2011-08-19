<div class="search_box">
    <form method="get" action="${c['url_manager'].get_search_form_action()}">
        <input type="text" name="q" value="${c['q']}"/>
        <input type="hidden" name="a" value="${c['url_manager'].get_form_field_args()}"/>
        <input type="submit" name="submit_search" value="Search"/>
    </form>
</div>

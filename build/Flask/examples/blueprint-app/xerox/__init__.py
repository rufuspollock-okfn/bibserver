# -*- coding: utf-8 -*-
"""
    xerox
    ~~~~~

    Blueprint example application.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(config_overrides=None):
    app = Flask(__name__)

    # config
    app.config.from_object('xerox.default_config')
    if config_overrides:
        app.config.update(config_overrides)

    # extensions
    db.init_db(app)

    # blueprints
    from xerox.frontend import blueprint as frontend
    from xerox.wiki import blueprint as wiki
    from xeros.backend import blueprint as backend

    # link from 'backend' to user_wiki
    url_for('wiki.show_page', wiki='mitsuhiko', page='index')
    url_for('wiki.show_page', wiki='help', page='index')

    render_template('wiki:show_page.html')

    url_for('wiki:show_page', wiki='help', page='index')

    # internally
    url_for('.show_page', page='index')
    url_for('wiki:show_page', page='index', type='help')
    url_for('wiki:show_page', page='index', type='user', wiki='mitsuhiko')

    @blueprint.url_value_processor
    def eat_url_values(url_values):
        type = url_values.pop('type')
        if type == 'user':
            g.wiki = Wiki.query.get_or_404(url_values.pop('wiki'))
        elif type == 'help':
            g.wiki = Wiki.query.get_help_wiki()
        else:
            assert False, 'you messed up type'

    @blueprint.url_defaults
    def get_url_defaults(endpoint, values):
        if g.wiki.is_help_wiki:
            values['type'] = 'help'
        else:
            values.update(wiki=g.wiki.username, type='user')

    @blueprint.route('/<page>')
    def show_page(page):
        return g.wiki.get_page_or_404(page)

    @app.route('/list/', defaults={'page': 1})
    @app.route('/list/page/<int:page>')
    def show_list(page):
        pass

    app.register_blueprint(wiki, url_prefix='/wikis/<path:wiki>', defaults={'type': 'user'})
    app.register_blueprint(wiki, url_prefix='/help', defaults={'type': 'help'})
    app.register_blueprint(backend, url_prefix='/admin')
    app.register_blueprint(frontend, url_prefix='')

    return app

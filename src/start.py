import os
from functools import lru_cache
from pathlib import Path

import yaml
from connexion import FlaskApp
from connexion.resolver import RelativeResolver
from dotenv import load_dotenv
from pony.orm import Database, set_sql_debug

from src.models import define_entities_game, define_entities_meta, define_entities_user
from src.services.enforcedefaults import validator_remap


@lru_cache()
def get_project_root():
    return Path(__file__).parent.parent


@lru_cache()
def get_project_version():
    """Get the current version from openapi.yml config file.
    """
    yml_path = Path(get_project_root(), 'openapi.yml')
    with open(yml_path, 'r') as fin:
        yml = yaml.safe_load(fin)

    return yml['info']['version']


@lru_cache()
def get_app():
    """Connexion Wrapper App
    Connexion creates a wrapper around a Flask app, through which all requests are passed.
    The Connexion wrapper app is called by wsgi.py and pytest.
    You can access the Flask app with `app.app.properties`.
    """

    # Load Environment Variables from dotenv file
    dotenv_path = Path(get_project_root(), '.env')
    load_dotenv(dotenv_path)

    # Todo: Sentry integration
    # sentry_sdk.init(
    #     dsn=os.environ.get('SENTRY_DSN'),
    #     integrations=[FlaskIntegration()],
    #     # Reduce this for production, maybe 0.25
    #     traces_sample_rate=0.25,
    #     release=get_project_version(),
    #     environment=Config().SENTRY
    # )

    swagger_options = {
        'swagger_url': '/',
        'swagger_ui_config': {
            'operationsSorter': 'method',
            'tagsSorter': 'alpha',
        }
    }
    connexion_app = FlaskApp(__name__, specification_dir=get_project_root(), options=swagger_options)
    connexion_app.add_api(
        'openapi.yml',
        resolver=RelativeResolver('src.views'),
        validate_responses=True,
        validator_map=validator_remap,
    )
    connexion_app.app.config.from_prefixed_env()
    return connexion_app


def get_db():
    """Bind Pony ORM to database
    """
    if os.environ.get('FLASK_DEBUG') == 0:  # production
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        passwd = os.environ.get('DB_PASSWORD')
        database = Database(provider='mysql', host=host, user=user, passwd=passwd, db='db_aleleio')
    else:  # development
        database = Database(provider='sqlite', filename='db_aleleio.sqlite', create_db=True)
    define_entities_game(database)
    define_entities_meta(database)
    define_entities_user(database)
    database.generate_mapping(create_tables=True)
    set_sql_debug(False)
    return database

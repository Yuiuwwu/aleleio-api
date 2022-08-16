from typing import List, Dict

import connexion
from flask import abort
from pony.orm import db_session

from src.services import search
from src.services.create import create_games
from src.start import get_db

db = get_db()


def get_all():
    query = connexion.request.values
    return search.all_games(query)


def create(games: List[Dict]):
    new_instances, errors = create_games(games)
    if errors:
        return {"errors": [e.__str__() for e in errors]}, 409
    return [game.to_schema_out() for game in new_instances], 201


@db_session
def get_single(game_id):
    game = db.Game.get(id=game_id)
    if game is None:
        abort(404)
    return game.to_schema_out()


def update_single():
    # Update in Github Games Repo
    # https://stackoverflow.com/a/61533333
    return "update_single"


@db_session
def delete_single(game_id):
    game = db.Game.get(id=game_id)
    if game is None:
        abort(404)
    game.delete()
    return {"success": f"Deleted game#{game_id}."}
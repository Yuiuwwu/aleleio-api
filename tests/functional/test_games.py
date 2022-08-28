import os
from copy import deepcopy

MIN_GAME = {'names': ['Bananas'], 'descriptions': ['This stuff is bananas, BANANAS!'], 'game_types': ['ice', 'song'],
            'game_lengths': ['short'], 'group_sizes': ['event']}
MAX_GAME = {'names': ['Monkey Circus', 'Dog Show'], 'descriptions': ['This game has two descriptions.', 'Second one'],
            'game_types': ['ice', 'song'], 'game_lengths': ['short'], 'group_sizes': ['event'],
            'group_needs': [{'slug': 'why', 'score': 4}], 'materials': ['bananas', 'bones'],
            'prior_prep': 'Prepare the area by hiding both, bananas and bones.',
            'exhausting': True, 'touching': True, 'scalable': True, 'digital': True,
            'license': {'name': 'Unlicense', 'url': 'https://unlicense', 'owner': 'alele.io', 'owner_url': 'alele.io'},
            'references': [{'name': 'Wikipedia', 'url': 'https://wikipedia.org/monkey_circus'}]}


def test_get_games(client):
    response = client.get('/games')
    assert response.status_code == 200


def test_create_games_with_complete_request(client):
    payload = [MIN_GAME]
    response = client.post('/games', json=payload)
    assert response.status_code == 201


def test_create_games_with_maximum_request(client):
    payload = [MAX_GAME]
    response = client.post('/games', json=payload)
    assert response.status_code == 201


def test_create_games_with_duplicate(client):
    payload = [MIN_GAME]
    response = client.post('/games', json=payload)
    assert response.status_code == 409
    assert response.json == {"errors": ["A game with the name 'bananas' exists already."]}


def test_create_games_empty_json(client):
    response = client.post('/games', json=[{}])
    assert response.status_code == 400
    assert 'is a required property' in response.text


def test_create_games_without_array(client):
    payload = MIN_GAME
    response = client.post('/games', json=payload)
    assert response.status_code == 400
    assert 'is not of type \'array\'' in response.text


def test_create_games_with_additional_properties(client):
    payload = deepcopy(MIN_GAME)
    payload['eek'] = 'A mouse!'
    response = client.post('/games', json=[payload])
    assert response.status_code == 400
    assert 'Additional properties are not allowed' in response.text


def test_get_single_game(client):
    response = client.get('/games/1')
    assert response.status_code == 200


def test_get_single_game_wrong_id(client):
    response = client.get('/games/99')
    assert response.status_code == 404


def test_update_games_with_empty_game_types(client):
    """Games need at least one game_type
    """
    payload = {"game_types": []}
    response = client.patch('/games/1', json=payload)
    assert response.status_code == 400
    assert '[] is too short - \'game_types\'' in response.text



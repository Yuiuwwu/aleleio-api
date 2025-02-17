"""
A script to write the games library on github (Markdown files with YAML frontmatter) to the database.
See docs/update-games-db.md for more detailed information.
"""
import os
import shutil
from typing import Union
from zipfile import ZipFile
from pathlib import Path

import yaml
from dotenv import load_dotenv

import frontmatter
import mistune
import requests as requests

from src.services import create
from src.start import run_startup_tasks, get_db


def get_games_from_github():
    """Download game repository via api.github.com and return filepaths inside.
    """
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root.joinpath('.env'))
    token = os.getenv('GITHUB_TOKEN')
    tmp_path = project_root.joinpath('tools', 'tmp')

    # Download zip file from github
    url = 'https://api.github.com/repos/aleleio/teambuilding-games/zipball'
    headers = {'Authorization': f'token {token}'}
    r = requests.get(url, headers=headers, allow_redirects=True)
    parts = r.headers.get('content-disposition').split(' ')
    download_name = parts[1][9:-4]
    zip_path = tmp_path.joinpath(f'{download_name}.zip')
    open(zip_path, 'wb').write(r.content)
    print(f'Downloaded zip repo to \"{zip_path}\"')

    # Unzip
    with ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(tmp_path)

    # Clean Up
    zip_path.unlink()
    print(f'Deleted zip file: \"{zip_path}\"')

    return tmp_path.joinpath(download_name)


def get_files_from_local(path):
    """Create a list of game.md filepaths
    """
    file_list = os.listdir(path)
    file_list = [path.joinpath(file) for file in file_list]
    return file_list


def convert_md_to_game(md):
    """Convert Markdown to GameIn object
    """
    md = frontmatter.load(md)

    if md.get('alias'):
        return None
    else:
        game = md.to_dict()
        game['names'] = list()
        game['descriptions'] = list()
        markdown = mistune.create_markdown(renderer='ast')
        tokens = markdown(game.get('content'))
        is_description = 0
        for token in tokens:
            if token['type'] == 'heading' and token['level'] == 1:
                game['names'].append(token['children'][0]['text'])
                is_description = 0
                continue
            elif token['type'] == 'heading' and token['children'][0]['text'] == 'Description':
                is_description = 1
                continue
            elif is_description > 0:
                if not token['type'] == 'list':
                    if is_description == 1:
                        game['descriptions'].append(token['children'][0]['text'])
                    elif is_description > 1:
                        previous_description = game['descriptions'].pop()
                        description = f"{previous_description}\n\n{token['children'][0]['text']}"
                        game['descriptions'].append(description)
                else:
                    # Todo: Make this better. This happens, when the token/paragraph starts with a '1.'
                    if is_description == 1:
                        game['descriptions'].append(token['children'][0]['children'][0]['children'][0]['text'])
                    elif is_description > 1:
                        previous_description = game['descriptions'].pop()
                        description = f"{previous_description}\n\n{token['children'][0]['children'][0]['children'][0]['text']}"
                        game['descriptions'].append(description)
                is_description += 1

        del game['content']

        return game


def write_games_to_database(games):
    """Insert the games into the database
    Todo: Make sure to update and not touch statistics, metadata etc. in the existing database
    """

    created_games, errors = create.create_games(games)
    print(f'Created ({len(created_games)}):', created_games)
    print(f'Errors ({len(errors)}):', errors)


def convert_yml_to_ref(ref_yml):
    """Convert Markdown to reference
    """
    references = []
    with open(ref_yml, 'r') as fin:
        ymls = yaml.safe_load_all(fin)
        for ref in ymls:
            ref['game_slug'] = ref.pop('refers_to')
            references.append(ref)
    return references


def write_references_to_database(references):
    """
    """
    created_refs, errors = create.create_references(references)
    print(f'Created ({len(created_refs)}):', created_refs)
    print(f'Errors ({len(errors)}):', errors)


def run_local():
    print('RUNNING IMPORT-TO-DATABASE LOCALLY')
    print('----------------------------------')
    project_root = Path(__file__).parent.parent
    local_games_folder = project_root.joinpath('tools', 'games')
    local_refs_folder = project_root.joinpath('tools', 'references')
    games = get_files_from_local(local_games_folder)
    refs = get_files_from_local(local_refs_folder)
    print(f'Reading games & references from {project_root}/tools/')
    return games, refs


def run_github():
    print('RUNNING IMPORT-TO-DATABASE FROM GITHUB')
    print('----------------------------------')
    download_folder = get_games_from_github()
    download_games_folder = download_folder.joinpath('games')
    download_refs_folder = download_folder.joinpath('references')
    games = get_files_from_local(download_games_folder)
    refs = get_files_from_local(download_refs_folder)
    print(f'Reading games & references from {download_folder}.')
    return games, refs


if __name__ == '__main__':
    game_paths, ref_paths = run_local()
    # game_paths, ref_paths = run_github()

    run_startup_tasks(get_db())

    game_list = []
    alias_list = []
    for md in game_paths:
        game = convert_md_to_game(md)
        if game is not None:
            game_list.append(game)
        else:
            alias_list.append(md)

    print()
    print('Writing games to database')
    write_games_to_database(game_list)

    print()
    print('Writing references to database')
    for yml in ref_paths:
        print(f"Reading from: {str(yml).split('/').pop()}")
        refs = convert_yml_to_ref(yml)
        write_references_to_database(refs)

    # Remove tmp/repo/ folder with games
    # shutil.rmtree(download_folder)


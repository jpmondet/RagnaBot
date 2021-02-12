""" Handles db access and abstracts functions
that can be (and should be) abstracted """

#! /usr/bin/env python3

from re import compile as rcompile, IGNORECASE as rIGNORECASE
from typing import List, Dict, Any
from os import access, R_OK
from time import sleep
from json import load as jload
from json.decoder import JSONDecodeError

from pymongo import MongoClient, ASCENDING as MDBASCENDING
from pymongo.errors import BulkWriteError, DuplicateKeyError as MDDPK
from requests import get as rget
import requests.exceptions

from utils.env import DB_STRING, RAGNASONG_MAPS, RAGNASONG_URL

DB_CLIENT = MongoClient(DB_STRING)
DB = DB_CLIENT.ragnabot
CUSTOM_SONGS_COLLECTION = DB.csongs
LBOARDS_COLLECTION = DB.cslboards
PENDING_SCORES_COLLECTION = DB.pending
ACCOUNTS_COLLECTION = DB.accounts     
INDEX_SEQUENCE = DB.index_seq

CUSTOM_SONGS: str = "custom_songs.json"
PLAYERS_DETAILS: str = "players.json"
PENDING_SCORES: str = "pending_scores.json"
ACCOUNTS: str = "id_accounts_list.json"

def _safe_load_json_file(filename: str):
    if not access(filename, R_OK):
        return None

    datas: List[Dict[str, Any]] = None
    try:
        with open(filename, 'r') as fp:
            datas = jload(fp)
    except JSONDecodeError:
        return None

    return datas
    
class NetworkError(RuntimeError):
    pass

def _retryer(max_retries=10, timeout=5):
    def wraps(func):
        request_exceptions = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.SSLError,
        )
        def inner(*args, **kwargs):
            for i in range(max_retries):
                try:    
                    result = func(*args, **kwargs)
                except request_exceptions:
                    sleep(timeout * i)
                    continue
                else:
                    return result
            else:
                raise NetworkError 
        return inner
    return wraps


def prep_db_if_not_exist():
    """ If db is empty, with try to fill it with flat json files we may have from previous
    iterations. """
    
    if (
        list(CUSTOM_SONGS_COLLECTION.find())
        and list(LBOARDS_COLLECTION.find())
        and list(ACCOUNTS_COLLECTION.find())
        and list(PENDING_SCORES_COLLECTION.find())
    ):
        # Looks like everything is already migrated
        # Leaving :)
        return


    print("Preping db with flat files since at least one collection is empty")

    pendings = _safe_load_json_file(PENDING_SCORES)
    if pendings:
        PENDING_SCORES_COLLECTION.insert_many(pendings)

    # We ensure that songs_id, leaderboard_ids and playerds_ids are unique : 
    # (this is a mongodb feature)
    CUSTOM_SONGS_COLLECTION.create_index([('uuid', MDBASCENDING)], unique=True)
    ACCOUNTS_COLLECTION.create_index([('discord_id', MDBASCENDING)], unique=True)
    INDEX_SEQUENCE.create_index([('id', MDBASCENDING)], unique=True)

    if not list(INDEX_SEQUENCE.find()):
        INDEX_SEQUENCE.insert_one({'id': 0})
    # Leaderboards are lil' more specific since they were stored in customs
    # Thus we have to do more processing here to extract lboards
    if not list(LBOARDS_COLLECTION.find()) or not list(CUSTOM_SONGS_COLLECTION.find()):

        # We leverage this migration to use data from 
        # Ragnasong website
    
        # First we get all the maps on the website
        rs_maps: List[Dict[str, Any]] = get_all_maps_from_api()
        # We add them to our db since this is the new source of truth
        try:
            CUSTOM_SONGS_COLLECTION.insert_many(rs_maps)
        except BulkWriteError as bwe:
            if 'E11000 duplicate key error collection' in str(bwe):
                pass
            else:
                print(bwe)
                return

        csongs = _safe_load_json_file(CUSTOM_SONGS)

        if csongs:
            # We try to get the old leaderboards to map them to the new source of truth is possible
            for cs in csongs:
                if cs['leaderboard']:
                    rsmap: Dict[str, Any] = get_map_by_name(cs['name'], cs['band'])
                    if not rsmap:
                        print(cs)
                        continue

                    # Instead of storage a list, we use the power of mongodb and just store records 
                    # Should help later to retrieve just what's needed and not the whole list
                    for score in cs['leaderboard']:
                        lb_to_add = score.copy()
                        lb_to_add['map_uuid'] = rsmap['uuid']
                        LBOARDS_COLLECTION.insert_one(lb_to_add)

    if not list(ACCOUNTS_COLLECTION.find()):
        acc = _safe_load_json_file(ACCOUNTS)
        players_details = _safe_load_json_file(PLAYERS_DETAILS)

        if acc and players_details:
            player_name_id = {}
            for pdetails in players_details:
                # We keep it temporary in player_name_id to migrate it to account just after
                pdetails['id'] = get_last_index_from_index_sequence()
                player_name_id[pdetails['name']] = pdetails

            # Take the chance to update the dict to be mongodb-friendly 
            # by adding an id instead of using a value as key
            acc_updated = []
            for discord_id, player_name in acc.items():
                pdetails = player_name_id[player_name]
                acc_updated.append(
                        {'discord_id': discord_id, 
                            'player_id': pdetails['id'], 'player_name': player_name, 'total_misses': 0, 'total_perfects_percent': 0.0, 'total_score': 0.0, 'total_triggers': 0})
            ACCOUNTS_COLLECTION.insert_many(acc_updated)

    # Now that we have migrated all data, we suppress redondant datas that are still in leaderboards collection
    scores = get_entire_collection(LBOARDS_COLLECTION)
    for score in scores:
        if not score.get('map_name'):
            continue
        score_updated = score.copy()
        account = get_account_by_discord_id(score['player_discord_id'])
        score_updated['player_id'] = account['player_id']
        score_updated['difficulty_played'] = score['difficulty']
        del(score_updated['map_name'])
        del(score_updated['band'])
        del(score_updated['mapper'])
        del(score_updated['player_name'])
        del(score_updated['player_discord_id'])
        del(score_updated['player_discord_name'])
        del(score_updated['difficulty'])
        #LBOARDS_COLLECTION.update_one(score, { '$set': score_updated })
        LBOARDS_COLLECTION.find_one_and_replace(score, score_updated )
        # We also take this chance to update account stats:
        account['total_score'] = float(account['total_score']) + float(score['score'])
        account['total_perfects_percent'] = float(account['total_perfects_percent']) + float(score['perfects_percent'])
        account['total_misses'] = int(account['total_misses']) + int(score['misses'])
        account['total_triggers'] = int(account['total_triggers']) + int(score['triggers'])
        del(account['_id'])
        update_multiple_value_on_account_by_player_id(account['player_id'],  account)



def get_entire_collection(mongodb_collection) -> List[Dict[str, Any]]:
    return mongodb_collection.find({})

def get_nb_documents(mongodb_collection) -> int:
    return mongodb_collection.count_documents({})

def get_last_index_from_index_sequence() -> int:
    nb_doc = get_nb_documents(INDEX_SEQUENCE)
    INDEX_SEQUENCE.insert_one({'id': nb_doc})
    return nb_doc

def get_account_by_discord_id(discord_id: int) -> Dict[str, Any]:
    return ACCOUNTS_COLLECTION.find_one({'discord_id': str(discord_id)})

def get_account_by_player_id(player_id: int) -> Dict[str, Any]:
    return ACCOUNTS_COLLECTION.find_one({'player_id': player_id})

def get_accounts() -> List[Dict[str, Any]]:
    return ACCOUNTS_COLLECTION.find({})

def get_pending_submissions() -> List[Dict[str, Any]]:
    return PENDING_SCORES_COLLECTION.find({})

def get_pending_submissions_by_player_id(player_id: int) -> List[Dict[str, Any]]:
    return PENDING_SCORES_COLLECTION.find({'player_id': player_id})

def get_map_by_name(title: str, artist: str) -> Dict[str, Any]:
    # This can be dangerous if there are multiple maps with the same name
    # It will be used only for migration purpose
    return CUSTOM_SONGS_COLLECTION.find_one({'title': title, 'artist': artist})

def get_scores_by_player_id(player_id: int) -> List[Dict[str, Any]]:
    return LBOARDS_COLLECTION.find({'player_id': player_id})

def get_score_by_map_uuid_and_diff(map_uuid: str, difficulty: str) -> List[Dict[str, Any]]:
    return LBOARDS_COLLECTION.find({'map_uuid': map_uuid, 'difficulty_played': difficulty})

def get_score_by_player_id_map_uuid_diff(player_id: int, map_uuid: str, difficulty: str) -> Dict[str, Any]:
    return LBOARDS_COLLECTION.find_one({'player_id': player_id, 'map_uuid': map_uuid, 'difficulty_played': difficulty})

def get_map_by_uuid(uuid: str) -> Dict[str, Any]:
    return CUSTOM_SONGS_COLLECTION.find_one({'uuid': uuid})

@_retryer()
def get_from_api(url: str) -> Dict[str, Any]:
    try:
        return rget(url).json()
    except JSONDecodeError:
        return {}

def get_all_maps_from_api() -> List[Dict[str, Any]]:
    try:
        start_count: int = 0
        resp: Dict[str, Any] = get_from_api(RAGNASONG_MAPS.format(start_count))
        nb_resp: int = len(resp["results"])
        rs_maps: List[Dict[str, Any]] = resp["results"]
        for start_count in range(nb_resp,resp["count"] + 1,nb_resp):
            resp = get_from_api(RAGNASONG_MAPS.format(start_count))
            rs_maps.extend(resp["results"])
        return rs_maps
    except NetworkError:
        return []

def get_new_maps_from_api() -> List[Dict[str, Any]]:
    current_maps = CUSTOM_SONGS_COLLECTION.find({})
    rs_maps = get_all_maps_from_api()

    current_maps_uuids = { dcm['uuid']: dcm for dcm in current_maps }
    rs_maps_uuids =  { dcm['uuid']: dcm for dcm in rs_maps }

    uuids_to_add = set(rs_maps_uuids.keys()).difference(set(current_maps_uuids.keys()))
    print(uuids_to_add)

    maps_to_add = [ rs_maps_uuids[uuid] for uuid in uuids_to_add ] 
    print(maps_to_add)

    return maps_to_add


def search_account_by_name(player_name: str):
    return ACCOUNTS_COLLECTION.find({ 'player_name': rcompile(player_name, rIGNORECASE)})

def search_map_by_title_artist_mapper(title: str, artist: str, mapper: str) -> List[Dict[str, Any]]:
    return CUSTOM_SONGS_COLLECTION.find( {
            "$and": [
                { 'title': rcompile(title, rIGNORECASE)},
                { 'artist': rcompile(artist, rIGNORECASE)},
                { 'ownerUsername': rcompile(mapper, rIGNORECASE)},
            ]
            })

def search_map_by_pattern(pattern: str):
    return CUSTOM_SONGS_COLLECTION.find( {
            "$or": [
                { 'uuid': rcompile(pattern, rIGNORECASE)},
                { 'title': rcompile(pattern, rIGNORECASE)},
                { 'artist': rcompile(pattern, rIGNORECASE)},
                { 'ownerUsername': rcompile(pattern, rIGNORECASE)},
                { 'difficulty': rcompile(pattern, rIGNORECASE)},
                { 'musicLink': rcompile(pattern, rIGNORECASE)},
            ]
            })

def add_account(account: Dict[str, Any]) -> None:
    ACCOUNTS_COLLECTION.insert_one(account)

def add_pending_submission(submission: Dict[str, Any]) -> None:
    PENDING_SCORES_COLLECTION.insert_one(submission)

def add_score_to_cslboard(submission: Dict[str, Any]) -> None:
    LBOARDS_COLLECTION.insert_one(submission)

def add_map_to_custom_songs(map_to_add: Dict[str, Any]) -> None:
    CUSTOM_SONGS_COLLECTION.insert_one(map_to_add)

def add_multiple_maps_to_custom_songs(maps_to_add: List[Dict[str, Any]]) -> None:
    CUSTOM_SONGS_COLLECTION.insert_many(maps_to_add)

def update_collection(mongodb_collection, mongo_cmd, match_query, replace_query) -> None:
    mongodb_collection.update_many(match_query, {mongo_cmd: replace_query})

def update_set_collection(mongodb_collection, match_query: Dict[str, Any], replace_query: Dict[str, Any]) -> None:
    update_collection(mongodb_collection, '$set', match_query, replace_query)

def update_multiple_value_on_account_by_player_id(player_id: int,  replace_query: Dict[str, Any]) -> None:
    update_set_collection(ACCOUNTS_COLLECTION, { 'player_id': player_id}, replace_query)

def update_account_by_player_id(player_id: int, attr_to_set: str, attr_value: Any) -> None:
    update_set_collection(ACCOUNTS_COLLECTION, { 'player_id': player_id}, { attr_to_set: attr_value })

def update_map_by_uuid(uuid: str, attr_to_set: str, attr_value: Any) -> None:
    update_set_collection(CUSTOM_SONGS_COLLECTION, { 'uuid': uuid }, { attr_to_set: attr_value })

def delete_account(player_id: int) -> None:
    ACCOUNTS_COLLECTION.delete_one({'player_id': player_id})

def delete_scores_on_lboard_by_player_id(player_id: int) -> None:
    LBOARDS_COLLECTION.delete_many({'player_id': player_id})

def delete_pending_submission(submission: Dict[str, Any]) -> None:
    PENDING_SCORES_COLLECTION.delete_one(submission)

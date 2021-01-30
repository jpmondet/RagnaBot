""" Handles db access and abstracts functions
that can be (and should be) abstracted """

#! /usr/bin/env python3

from re import compile as rcompile, IGNORECASE as rIGNORECASE

from utils.bot_utils import *
from pymongo.errors import BulkWriteError, DuplicateKeyError as MDDPK
from requests import get as rget

def prep_db_if_not_exist():
    """ If db is empty, with try to fill it with flat json files we may have from previous
    iterations. """

    print("Preping db with flat files since at least one collection is empty")

    with open(PENDING_SCORES, 'r') as fp:
        pendings = jload(fp)
    if pendings:
        PENDING_SCORES_COLLECTION.insert_many(pendings)

    # We ensure that songs_id, leaderboard_ids and playerds_ids are unique : 
    # (this is a mongodb feature)
    CUSTOM_SONGS_COLLECTION.create_index([('id', MDBASCENDING)], unique=True)
    ACCOUNTS_COLLECTION.create_index([('discord_id', MDBASCENDING)], unique=True)
    INDEX_SEQUENCE.create_index([('id', MDBASCENDING)], unique=True)

    if not list(INDEX_SEQUENCE.find()):
        INDEX_SEQUENCE.insert_one({'id': 0})
    # Leaderboards are lil' more specific since they were stored in customs
    # Thus we have to do more processing here to extract lboards
    if not list(LBOARDS_COLLECTION.find()) or not list(CUSTOM_SONGS_COLLECTION.find()):
        with open(CUSTOM_SONGS, 'r') as fp:
            csongs = jload(fp)

        # We leverage this migration to use data from 
        # Ragnasong website
    
        # First we get all the maps on the website
        start_count: int = 0
        resp: Dict[str, Any] = rget(RAGNASONG_MAPS.format(start_count)).json()
        nb_resp: int = len(resp["results"])
        rs_maps: List[Dict[str, Any]] = resp["results"]
        for start_count in range(nb_resp,resp["count"] + 1,nb_resp):
            resp = rget(RAGNASONG_MAPS.format(start_count)).json()
            rs_maps.extend(resp["results"])
        # We add them to our db since this is the new source of truth
        try:
            CUSTOM_SONGS_COLLECTION.insert_many(rs_maps)
        except BulkWriteError as bwe:
            if 'E11000 duplicate key error collection' in str(bwe):
                pass
            else:
                print(bwe)
                return


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
        with open(ACCOUNTS, 'r') as fp:
            acc = jload(fp)

        with open(PLAYERS_DETAILS, 'r') as fp:
            players_details = jload(fp)

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
                        'player_id': pdetails['id'], 'player_name': player_name, 'total_misses': pdetails['total_misses'], 'total_perfects_percent': pdetails['perfects_percent_avg'], 'total_score': pdetails['total_score'], 'total_triggers': pdetails['total_triggers']})
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

def search_account_by_name(player_name: str):
    return ACCOUNTS_COLLECTION.find({ 'player_name': rcompile(player_name, rIGNORECASE)})

def search_map_by_title_artist_mapper(title: str, artist: str, mapper: str) -> List[Dict[str, Any]]:
    return CUSTOM_SONGS_COLLECTION.find( {
            "$and": [
                { 'title': rcompile(pattern, rIGNORECASE)},
                { 'artist': rcompile(pattern, rIGNORECASE)},
                { 'ownerUsername': rcompile(pattern, rIGNORECASE)},
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

""" Handles db access and abstracts functions
that can be (and should be) abstracted """

#! /usr/bin/env python3

from utils.bot_utils import *
from pymongo.errors import BulkWriteError, DuplicateKeyError as MDDPK

# TODO: Add 'maps played' collection and fill it

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
    LBOARDS_COLLECTION.create_index([('id', MDBASCENDING)], unique=True)
    PLAYERS_DETAILS_COLLECTION.create_index([('id', MDBASCENDING)], unique=True)
    ACCOUNTS_COLLECTION.create_index([('discord_id', MDBASCENDING)], unique=True)

    with open(ACCOUNTS, 'r') as fp:
        acc = jload(fp)
    if not list(ACCOUNTS_COLLECTION.find()):
        # Take the chance to update the dict to be mongodb-friendly 
        # by adding an id instead of using a value as key
        acc_updated = []
        for discord_id, player_name in acc.items():
            acc_updated.append({'discord_id': discord_id, 'player_name': player_name})
        ACCOUNTS_COLLECTION.insert_many(acc_updated)


    with open(PLAYERS_DETAILS, 'r') as fp:
        players_details = jload(fp)
    if not list(PLAYERS_DETAILS_COLLECTION.find()):
        try:
            PLAYERS_DETAILS_COLLECTION.insert_many(players_details)
        except BulkWriteError as bwe:
            if 'E11000 duplicate key error collection' in str(bwe):
                pass
            else:
                print(bwe)
                return

    # Leaderboards are lil' more specific since they were stored in customs
    # Thus we have to do more processing here to extract lboards
    if not list(LBOARDS_COLLECTION.find()):
        with open(CUSTOM_SONGS, 'r') as fp:
            csongs = jload(fp)

        for cs in csongs:
            # We keep the same id of the song to help my brain xD
            # (this is not mandatory tho)
            lb_to_add = { 'id': cs['id'], 'leaderboard': cs['leaderboard']}
            try:
                LBOARDS_COLLECTION.insert_one(lb_to_add)
            except MDDPK:
                pass
            # Now we update the song so leaderboard is just an id to the proper
            # leaderboard (this is why it wasn't mandatory above)
            cs['leaderboard'] = cs['id']

        try:
            CUSTOM_SONGS_COLLECTION.insert_many(csongs)
        except BulkWriteError as bwe:
            if 'E11000 duplicate key error collection' in str(bwe):
                pass
            else:
                print(bwe)
                return


def load_accounts():
    """ Loads registered discord ids accs from files and return the associated dict """
    return list(ACCOUNTS_COLLECTION.find())

def get_account(author_id: int):
    return ACCOUNTS_COLLECTION.find_one({'discord_id': str(author_id)})

def add_account(author_id: int, player_name: str):
    ACCOUNTS_COLLECTION.insert_one({'discord_id': str(author_id), 'player_name': player_name})

def add_player(new_player: Dict[str, Any]):
    last_id = PLAYERS_DETAILS_COLLECTION.count_documents({})
    new_player["id"] =  last_id + 1
    new_player["maps_played"] = last_id + 1 # We try to map ids to keep things simple
    PLAYERS_DETAILS_COLLECTION.insert_one(new_player)

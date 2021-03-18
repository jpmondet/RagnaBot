""" Compute (or middle, or controller) layer that does
treatments on data retrieved from the db layer depending 
on what users asked for on discord (via cogs) """

#! /usr/bin/env python3

from typing import List, Dict, Any, Union
from collections import defaultdict

import storage.db_layer as dbl

#TODO: Use caching instead to retrieve from the db directly each time

def check_backend() -> bool:

    try:
        dbl.prep_db_if_not_exist()
    except Exception as err:
        print(err)
        return False

    return True


def get_top_players(nb_to_show: int, format=True) -> Union[str, List]:

    accounts: List[Dict[str, Any]] = list(dbl.get_accounts())
    
    top_players: str = "\n"
    top_players_list: List[Dict[str, Any]] = []
    
    if len(accounts) <= nb_to_show:
        nb_to_show = len(accounts)
    
    print("Nb players to show:", nb_to_show)
    
    sorted_accs = sorted(accounts, key=lambda k: float(k['total_score']), reverse=True)

    
    for rank, account in enumerate(sorted_accs):
        if nb_to_show <= 0:
            break
        print(rank, account)
        nb_player_scores = len(list(dbl.get_scores_by_player_id(account['player_id'])))
        nb_songs_played = nb_player_scores
        if not nb_player_scores:
            nb_player_scores = 1
        perfects_percent_avg: float = account['total_perfects_percent'] / nb_player_scores
        top_players_list.append({ "rank": f"{str(rank+1)}", "player_name": f"{account['player_name']}", "total_score": f"{account['total_score']:.2f}", "total_misses": f"{str(account['total_misses'])}", "perfects_percent_avg": f"{str(perfects_percent_avg)}%", "total_triggers": f"{str(account['total_triggers'])}", "nb_songs_played": f"{str(nb_songs_played)}"})
        top_players += f"{str(rank+1)} - {account['player_name']} : {account['total_score']:.2f} ({str(account['total_misses'])} misses, {str(perfects_percent_avg)}%, {str(account['total_triggers'])} triggers on {str(nb_songs_played)} maps played) \n"
        nb_to_show -= 1

    if not format:
        return top_players_list
    return top_players

def get_top_players_on_specific_map(map_name: str, nb_to_show: int, format=True) -> Union[str, List]:

    if not map_name:
        return 'Please, specify at least a word (will try to find corresponding maps loosely) or an uuid :-) '

    matching_songs = list(dbl.search_map_by_pattern(map_name))

    leaders: str = ""
    leaders_dict: Dict[List[Dict[str, Any]]] = defaultdict(list)

    if not matching_songs:
        return 'Sorry, no maps were found with this pattern'

    #If there is more than 1 maps with this pattern, showing only the first
    matching_song: Dict[str, Any] = matching_songs[0]

    nb_to_show_temp: int = 0

    song_name = f"{matching_song['artist']} - {matching_song['title']} - {matching_song['ownerUsername']}"

    for difficulty in matching_song['difficulty'].split(','):
        map_scores_unsorted = list(dbl.get_score_by_map_uuid_and_diff(matching_song['uuid'], difficulty))
        print(map_scores_unsorted)
        map_scores = sorted(map_scores_unsorted, key=lambda k: k['score'], reverse=True)

        leaders += f"{song_name} - Level {difficulty}: \n"
        if len(map_scores) <= nb_to_show:
            nb_to_show_temp = len(map_scores)
        for rank, map_score in enumerate(map_scores):
            account = dbl.get_account_by_player_id(map_score['player_id'])
            if nb_to_show_temp <= 0:
                break
            leaders += f"        {str(rank+1)} - {account['player_name']} - {map_score['score']} ({str(map_score['misses'])} misses, {str(map_score['perfects_percent'])}%, {str(map_score['triggers'])} triggers) \n"
            leaders_dict[f"{song_name} - Level {difficulty}"].append({"rank": f"{str(rank+1)}", "player_name": f"{account['player_name']}", "score": f"{map_score['score']}", "misses": f"{str(map_score['misses'])}", "perfects_percent": f"{str(map_score['perfects_percent'])}%", "triggers": f"{str(map_score['triggers'])}"})
            nb_to_show_temp -= 1
    leaders += "\n"

    if not format:
        return leaders_dict
    return leaders


def registering_player(discord_id: int, discord_name: str, player_name: str) -> str:

    if not player_name:
        return 'Please indicate your in-game name. Exple : `!register "OMDN | Gneuh [knee-uh]"` (yeah, use quote if there are spaces & stuff !)'

    account = dbl.get_account_by_discord_id(discord_id)
    if account:
        return f"Uh? Looks like you're already registered as `{account['player_name']}`\n \
    If you wanna rename yourself, please use `!rename Your-new-in-game-name.` \n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)"

    # We get the next player_id available
    id_player = dbl.get_last_index_from_index_sequence()

    # We also add player's details
    account: Dict[str, Any] = {
        "discord_id": str(discord_id),
        "discord_name": discord_name,
        "player_id": id_player,
        "player_name": player_name,
        "total_misses": 0,
        "total_perfects_percent": 0.0,
        "total_score": 0,
        "total_triggers": 0,
    }

    dbl.add_account(account)

    return "Ok, you're correctly registered :slight_smile:"

def unregistering_player(discord_id: int, discord_name: str, confirm: str) -> str:

    if confirm != "YEAHIMSURE!":
        return f"{discord_name} didn't confirm, cancelling (send `!unregister YEAHIMSURE!` to confirm)"

    account = dbl.get_account_by_discord_id(discord_id)
    print(discord_id, account)
    if not account:
        return "Hmm, looks like there was an issue unregistering :thinking:"

    player_name: str = account['player_name']
    print(f"Performing unregister of {discord_id}'s account: {player_name}")

    dbl.delete_scores_on_lboard_by_player_id(account['player_id'])
    dbl.delete_account(account['player_id'])

    return f"Byee, no more scores from {player_name} :'("

def rename_player(discord_id: int, new_name: str) -> str:
    
    if not new_name:
        return f'Please specify the new name (with quotes if there are spaces). \n \
    Exple: `!rename "Awesome New Name"`'

    account = dbl.get_account_by_discord_id(discord_id)
    
    print(discord_id, account)
    if not account:
        return "Hmm, looks like this discord user doesn't have an account"

    player_name: str = account['player_name']
    print(f"Renaming {discord_id}'s account: {player_name} to {new_name}")

    player_id = account['player_id']
    dbl.update_account_by_player_id(player_id, 'player_name', new_name)

    return f"Byee {player_name} and welcome {new_name} :-)"


def search_accounts_by_pattern(player_name: str) -> Dict[str, Any]:
    return list(dbl.search_account_by_name(player_name))


def search_players_names_by_name_pattern(pattern: str, format=True) -> str:
    if not pattern:
        return "Please specify a word to find. For exemple !searchplayer gneuh should find the player with \n \
this word in the name"

    accounts = search_accounts_by_pattern(pattern)
    if not accounts:
        return "No player found with that pattern, sorry"
    
    if format:
        return "\n".join((account['player_name'] for account in accounts))
    
    return [account['player_name'] for account in accounts]

def get_player_stats(discord_id: int = 0, player_name: str = "", format=True) -> Union[str, Dict]:

    account: Dict[str, Any] = None
    if not player_name:
        print("Player name not in parameter. We look for the author of the message")
        account = dbl.get_account_by_discord_id(discord_id)
        if not account:
            print(f"No account registered for the discord id {discord_id}")
            return f"No account registered for the discord id {discord_id}"
        print(f"Ok, the author is registered as {account['player_name']}")
    else:
        # We search for the player passed in param
        accounts = list(dbl.search_account_by_name(player_name))
        if not accounts:
            print("No player found with that pattern")
            return "No player found with that name pattern"
        if len(accounts) > 1:
            print('The request found more than 1 player. Showing the first one')
        account = accounts[0]

    nb_player_scores = len(list(dbl.get_scores_by_player_id(account['player_id'])))
    if not nb_player_scores:
        nb_player_scores = 1

    nb_songs_played: int = nb_player_scores
    perfects_percent_avg: float = account['total_perfects_percent'] / nb_player_scores

    if not format:
        return { "player_name": f"{account['player_name']}", "total_score": f"{account['total_score']:.2f}", "total_misses": f"{str(account['total_misses'])}", "perfects_percent_avg": f"{str(perfects_percent_avg)}%", "total_triggers": f"{str(account['total_triggers'])}", "nb_songs_played": f"{str(nb_songs_played)}"}

    pstats_str: str = ""
    total_score: float = account['total_score']
    total_misses: int = account['total_misses']
    total_triggers: int = account['total_triggers']
    pstats_str =  f"{account['player_name']}\n\t \
Total score: {total_score:.2f},\n\t \
Total misses: {total_misses},\n\t \
Total triggers: {total_triggers},\n\t \
Perfects percent average: {perfects_percent_avg:.2f},\n\t \
On {nb_songs_played} maps played"
    print(pstats_str)
    return pstats_str


def get_formatted_maps_by_pattern(pattern: str) -> str:

    maps_found = dbl.search_map_by_pattern(pattern)

    output: str = ""

    for map_found in maps_found:
        uuid: str = map_found['uuid']
        diff: str = map_found['difficulty']
        diff1: str = diff.split(',')[0]
        output += "\n\nFound map : "
        output += f"{uuid} - {map_found['artist']} - {map_found['title']} - {map_found['ownerUsername']} (level(s): {diff})"
        output += "\n\nThis map is '!submit'-able with the following command:\n"
        output += f"!submit https://proof UUID(hash) LEVEL YOUR_SCORE NB_MISSES PERFECT_PERCENT NB_TRIGGERS"
        output += "\nFor example: "
        output += f"!submit https://me.com/img.png {uuid} {diff1} 1234 3 86 7"
    
    return output

def get_pendings_submissions(discord_id: int = 0) -> str:
    pendings: List[Dict[str, Any]] = None

    if discord_id:
        account = dbl.get_account_by_discord_id(discord_id)
        pendings = list(dbl.get_pending_submissions_by_player_id(account['player_id']))
    else:
        pendings = list(dbl.get_pending_submissions())    

    return pendings

def cancel_submission_of_player(discord_id: int = 0, id_submission: int = 0, api_call=False) -> str:

    pendings = get_pendings_submissions(discord_id)

    if not pendings:
        return []

    if not api_call:
        id_submission = id_submission - 1

    try:
        try_d = int(id_submission)
        if try_d >= len(pendings):
            raise ValueError
    except ValueError:
        if not api_call:
            return -1
        return "Submission id should be an int and not greater than the number of subs - 1"


    psub_to_cancel = pendings[id_submission]
    del(psub_to_cancel['_id'])

    print("Sub to cancel", psub_to_cancel)
    dbl.delete_pending_submission(psub_to_cancel)

    return str(psub_to_cancel)


def get_pending_subs_player(discord_id: int = 0, format=True) -> Union[str, Dict[int, Dict[str, Any]]]:

    pendings = get_pendings_submissions(discord_id)

    if not pendings:
        return []

    if format:
        output: str = ""
    else:
        output: List[Dict[int, Dict[str, Any]]] = defaultdict(list)

    for id_req, pdetails in enumerate(pendings):
        print(id_req, pdetails)
        map_submitted = dbl.get_map_by_uuid(pdetails['map_uuid'])
        print(map_submitted)
        account = dbl.get_account_by_player_id(pdetails['player_id'])
        print(account)
        if format:
            pdetails_str: str = f"        In-game name: {account['player_name']}  (Discord user : {account['discord_name']})" + '\n'
            pdetails_str += f"        Map played: {map_submitted['artist']} - "
            pdetails_str += f"{map_submitted['title']} - "
            pdetails_str += f"{map_submitted['ownerUsername']} "
            pdetails_str += f"(map uuid: {map_submitted['uuid']})" + '\n'
            pdetails_str += f"        score: {pdetails['score']} - "
            pdetails_str += f"misses: {pdetails['misses']} - "
            pdetails_str += f"perfects_percent: {pdetails['perfects_percent']} - "
            pdetails_str += f"triggers: {pdetails['triggers']}" + "\n"
            pdetails_str += f"        proof: {pdetails['proof']}" + "\n"
            print(pdetails_str)
            output += f"{id_req + 1} :\n{pdetails_str}\n"
        else:
            output[id_req].append(
                {"player_name": f"{account['player_name']}",
                "discord_name": f"{account['discord_name']}",
                "score": f"{pdetails['score']}",
                "misses": f"{pdetails['misses']}",
                "perfects_percent": f"{pdetails['perfects_percent']}",
                "triggers": f"{pdetails['triggers']}",
                "proof": f"{pdetails['proof']}",
                "map_uuid": f"{map_submitted['uuid']}",
                "artist": f"{map_submitted['artist']}",
                "title": f"{map_submitted['title']}",
                "ownerUsername": f"{map_submitted['ownerUsername']}",
                }
            )

    return output

def check_if_registered(discord_id: int) -> Dict[str, Any]:
    return dbl.get_account_by_discord_id(discord_id)

def attributes_presence(attributes: List[str]) -> bool:
    for attr in attributes:
        print(attr)
        if not attr:
            return False
    
    return True

def check_ldscore_parameters_submitted(proof: str, difficulty: str, score: str, misses: str, perfects_percent: str, triggers: str):

    if 'http' not in proof:
        return "The proof should be a link to an img or a video (you can paste your image to discord and just copy the link (including https://) to the message)"

    try:
        try_d = int(difficulty)
        if try_d < 1 or try_d > 20:
            raise ValueError
    except ValueError:
        return "Difficulty should be a number between 1 and...20? ;-)"

    try:
        try_d = float(score)
        if try_d < 0:
            raise ValueError
    except ValueError:
        return "Score should be a number (can be decimal) and be positive ;-)"

    try:
        try_d = int(misses)
        if try_d < 0:
            raise ValueError
    except ValueError:
        return "Misses should be a number and be positive ;-)"

    try:
        try_d = int(triggers)
        if try_d < 0:
            raise ValueError
    except ValueError:
        return "Triggers should be a number and be positive ;-)"

    try:
        try_d = float(perfects_percent)
        if try_d < 0:
            raise ValueError
    except ValueError:
        return "Perfects percentage should be a number (can be decimal) and be positive ;-)"

    return ""

def check_submission_by_name(
        proof: str = "",
        map_name: str = "",
        band: str = "",
        mapper: str = "",
        difficulty: str = "",
        score: str = "",
        misses: str = "",
        perfects_percent: str = "",
        triggers: str = "",
    ):

    if not attributes_presence(locals().values()):
        raise AttributeError("Please fill all the field so admins can verify your submission easily :-). \n \
Your submission should look like : !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
For example : `!submit-by-map-name https://image-or-video-proof.rocks Vodka Korpiklaani Vred 5 7777 1 99 3`")

def check_submission_by_uuid(
        proof: str = "",
        uuid: str = "",
        difficulty: str = "",
        score: str = "",
        misses: str = "",
        perfects_percent: str = "",
        triggers: str = "",
    ):

    if not attributes_presence(locals().values()):
        raise AttributeError("Please fill all the field so admins can verify your submission easily :-). \n \
Your submission should look like : !submit proof uuid difficulty score misses perfects_percent triggers \n \
For example : `!submit https://weblink/proof.png 46df5d714b99306e0a31d60970703733c72c3efc 6 7777 1 99 3`")

def check_submission(
        uuid: str = "",
        proof: str = "",
        map_name: str = "",
        band: str = "",
        mapper: str = "",
        difficulty: str = "",
        score: str = "",
        misses: str = "",
        perfects_percent: str = "",
        triggers: str = "",
        ctx: str = "",
    ):
    map_submitted: Dict[str, Any] = {}
    try:
        if uuid == "map":
            check_submission_by_name(proof,map_name,band,mapper,difficulty,score, misses,perfects_percent,triggers)
            map_submitted = list(dbl.search_map_by_title_artist_mapper(map_name, band, mapper))
            if not map_submitted:
                raise AttributeError("Sorry, not maps were found with those artist/title/mapper. Please try to search your map with `!searchmap 'anything'` before submitting")
            if len(map_submitted) > 1:
                raise AttributeError("Hmm, looks like there are multiple maps with those artist/title/mapper.  \n \
                    Please try to search your map with `!searchmap 'anything'` to submit with uuid instead")
            map_submitted = map_submitted[0]
        else:
            check_submission_by_uuid(proof,uuid,difficulty,score, misses,perfects_percent,triggers)
            map_submitted = dbl.get_map_by_uuid(uuid)
            if not map_submitted:
                raise AttributeError("Sorry, not maps were found with this uuid. Please try to search your map with `!searchmap 'anything'`")
        
        parameter_error = check_ldscore_parameters_submitted(proof, difficulty, score, misses, perfects_percent, triggers)
        if parameter_error:
            raise AttributeError(parameter_error)

        # Is difficulty submitted really coherent?
        if str(difficulty) not in map_submitted['difficulty']:
            raise AttributeError(f"Sorry, the map's difficulty you submitted doesn't exist. This map only have those : {map_submitted['difficulty']}") 
    except AttributeError as ae:
        raise AttributeError(str(ae))
    return map_submitted

def add_discord_name_to_account(discord_id: int, discord_name: str):
    account = dbl.get_account_by_discord_id(discord_id)
    player_id = account['player_id']
    dbl.update_account_by_player_id(player_id, 'discord_name', discord_name)
    return account
        

def handle_player_submission(
        discord_id: int,
        discord_name: str,
        proof: str = "",
        difficulty: str = "",
        score: str = "",
        misses: str = "",
        perfects_percent: str = "",
        triggers: str = "",
        map_name: str = "",
        band: str = "",
        mapper: str = "",
        uuid: str = "map",
    ):

    try:
        map_submitted = check_submission(uuid,proof,map_name,band,mapper,difficulty,score, misses,perfects_percent,triggers)
        # We take this chance to update player_discord_name because
        # we may not have it already (or it could have changed)
        account = add_discord_name_to_account(discord_id, discord_name)

        # Ok submission seems valid from the backend point of view
        # We push it to admins to verify the proof 
        # (can't identify anything on an image or video for now xD )
        submission: Dict[str, Any] = {}
        submission['map_uuid'] = map_submitted['uuid']
        submission['player_id'] = account['player_id']
        submission['difficulty_played'] = difficulty
        submission['score'] = score
        submission['misses'] = misses
        submission['perfects_percent'] = perfects_percent
        submission['triggers'] = triggers
        submission['proof'] = proof

        dbl.add_pending_submission(submission)

        return "Your request is correctly submitted. Please wait for an admin to verify your submission"
    except AttributeError as ae:
        return str(ae)


def validate_submission(id_pending: int = -1, api_call=False):

    if id_pending < 0:
        return "Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!valid 23`"

    pendings = get_pendings_submissions()
    if not pendings:
        return "Looks like there isn't any pending submission"

    if not api_call:
        id_pending = id_pending - 1

    try:
        try_d = int(id_pending)
        if try_d >= len(pendings):
            raise ValueError
    except ValueError:
        return "The submission id should be a number and between 1 and the number of pending submissions you have ;-)"


    valid_score: Dict[str, Any] = pendings[id_pending]

    print("Valid score found:", valid_score)
    del(valid_score['_id'])

    dbl.delete_pending_submission(valid_score)

    # Check if a score already exists for this map & player
    old_score = dbl.get_score_by_player_id_map_uuid_diff(valid_score['player_id'], valid_score['map_uuid'], valid_score['difficulty_played'])
    if old_score:
        print(old_score)
        if float(valid_score['score']) < float(old_score['score']):
            return "Looks like the player already has a better score for this map/difficulty"

    dbl.add_score_to_cslboard(valid_score)

    misses: int = int(valid_score['misses'])
    triggers: int = int(valid_score['triggers'])
    score: float = float(valid_score['score'])
    perfects_percent: float = float(valid_score['perfects_percent'])

    if old_score:
        misses -= int(old_score['misses'])
        triggers -= int(old_score['triggers'])
        score -= float(old_score['total_score'])
        perfects_percent -= float(old_score['perfects_percent'])

    player_id: int = valid_score['player_id']
    account: Dict[str, Any] = dbl.get_account_by_player_id(player_id)

    account['total_misses'] = int(account['total_misses']) + misses
    account['total_triggers'] = int(account['total_triggers']) + triggers
    account['total_score'] = float(account['total_score']) + score
    account['total_perfects_percent'] = float(account['total_perfects_percent']) + perfects_percent

    del(account['_id'])
    dbl.update_multiple_value_on_account_by_player_id(player_id, account)

    return "Score is correctly saved and leaderboards are correctly updated."


def force_update_maps() -> str:

    output: str = ""

    maps_to_add: List[Dict[str,Any]] = dbl.get_new_maps_from_api()

    if maps_to_add:
        output = f"Added : {str(len(maps_to_add))} maps from Ragnasong.com\n"
        dbl.add_multiple_maps_to_custom_songs(maps_to_add)

    return output
""" Compute (or middle, or controller) layer that does
treatments on data retrieved from the db layer depending 
on what users asked for on discord (via cogs) """

#! /usr/bin/env python3


import storage.db_layer as dbl


def check_backend() -> bool:

    try:
        dbl.prep_db_if_not_exist()
    except Exception as err:
        print(err)
        return False

    return True


def get_top_players(nb_to_show: int):
    accounts = list(dbl.get_accounts())
    
    top_players: str = "\n"
    
    if len(accounts) <= nb_to_show:
        nb_to_show = len(accounts)
    
    print("Nb players to show:", nb_to_show)
    
    sorted_accs = sorted(accounts, key=lambda k: float(k['total_score']), reverse=True)
    
    for rank, account in enumerate(sorted_accs):
        if nb_to_show <= 0:
            break
        print(rank, account)
        nb_player_scores = len(list(get_scores_by_player_id(account['player_id'])))
        perfects_percent_avg: float = account['total_perfects_percent'] / nb_player_scores
        top_players += f"{str(rank+1)} - {account['player_name']} : {account['total_score']:.2f} ({str(account['total_misses'])} misses, {str(perfects_percent_avg)}%, {str(account['total_triggers'])} triggers) \n"
        nb_to_show -= 1

    return top_players

#def get_top_players_on_specific_map(map_name: str, nb_to_show: int):



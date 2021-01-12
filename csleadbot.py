""" Discord bot """

#! /usr/bin/env python3

import os
import subprocess
import json
import requests
import discord
from discord.ext import commands
from typing import Dict, List, Any

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv("DISCORD_TOKEN")
GUILD: str = os.getenv('DISCORD_GUILD')
ROLE_ADMIN: str = os.getenv('ROLE_ADMIN')

CUSTOM_SONGS: str = "custom_songs.json"
PLAYERS_DETAILS: str = "players.json"
PENDING_SCORES: str = "pending_scores.json"
ACCOUNTS: str = "id_accounts_list.json"

# UTILS (NON-BOT FUNCTIONS)

def load_accounts():
    """ Loads registered discord ids accs from files and return the associated dict """
    id_accounts: Dict[str, str] = {}

    with open(ACCOUNTS, 'r') as facc:
        id_accounts = json.load(facc)
    
    return id_accounts

def paginate(lines, prefix='```css\n', suffix='```', chars=1850):
    """ Paginate long outputs since discord limits to 2000 chars... """
    size = 0
    message = [prefix]
    for line in lines:
        if len(line) + size > chars:
            message.append(suffix)
            yield message
            message = [prefix]
            size = 0
        message.append(line)
        size += len(line)
    message.append(suffix)
    yield message

async def record_usage(ctx):
    print(f"{ctx.author} asked for {ctx.message.content} on chan {ctx.channel} of {ctx.guild} at {ctx.message.created_at}")

# BOT FUNCTIONS START HERE
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and ready to get cmds')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send("Sorry, this command is not available in DMs.")
        return
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Sorry, you do not have the correct role for this command.')
        return
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send("Sorry, we have to limit this command to 1 use every 60 seconds...")
        return
        
@bot.command(name='top', help='Shows the current top10 overall')
@commands.before_invoke(record_usage)
async def top(ctx, nb_to_show: int = 10):

    for message in paginate("Not Implemented Yet"):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

    #print("Starting to get overall leaderboard")

    #players_details: List[Dict[str, Any]] = []
    #with open(PLAYERS_DETAILS) as pfile:
    #    players_details = json.load(pfile)

    #top_players: str = "\n"

    #if len(players_details) <= nb_to_show:
    #    nb_to_show = len(players_details)

    #print("Nb players to show:", nb_to_show)
    #
    #for rank, pdetails in enumerate(players_details):
    #    if nb_to_show <= 0:
    #        break
    #    print(rank, pdetails)
    #    top_players += f"{str(rank+1)} - {pdetails['name']} : {pdetails['total_score']}\n"
    #    nb_to_show -= 1

    #for message in paginate(top_players):
    #    msg_to_send = ''.join(message)
    #    await ctx.send(msg_to_send)

@bot.command(name='topmap', help='Shows the current top on a specific map')
@commands.before_invoke(record_usage)
async def top_map(ctx, map_name: str = "", nb_to_show: int = 10):
    print("Starting to get map leaderboard")

    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)

    matching_songs: List[Dict[str, Any]] = []
    for cs in custom_songs:
        if map_name in cs['full_name']:
            matching_songs.append(cs)

    print("Found matching songs:", matching_songs)
    names_songs =  ',\n\t'.join([cs['full_name'] for cs in matching_songs])
    match_str: str= f"Your request matched these songs :\n\t{names_songs}. \n \
\nHere are the associated leaderboards : \n\n"
    print(match_str)

    leaders: str = ""
    nb_to_show_temp: int = 0
    for cs in matching_songs:
        leaders += f"{cs['full_name']}: \n"
        if len(cs['leaderboard']) <= nb_to_show:
            nb_to_show_temp = len(cs['leaderboard'])
        for rank, player in enumerate(cs['leaderboard']):
            if nb_to_show_temp <= 0:
                break
            leaders += f"        {str(rank+1)} - {player['player_name']} - {player['score']} ({str(player['misses'])} misses, {str(player['perfects_percent'])}%, {str(player['triggers'])} triggers) \n"
            nb_to_show_temp -= 1
        leaders += "\n"

    for message in paginate(match_str + leaders):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='register', help='Register your in-game name (will be used to validate your proofs)')
@commands.before_invoke(record_usage)
async def register(ctx, player_name: str = ""):

    if not player_name:
        await ctx.send('Please indicate your in-game name. Exple : `!register "OMDN | Gneuh [knee-uh]"` (yeah, use quote if there are spaces & stuff !)')
        return

    id_accounts: Dict[str, str] = load_accounts()

    if id_accounts.get(str(ctx.author.id)):
        await ctx.send(f"Uh? Looks like you're already registered as `{id_accounts.get(str(ctx.author.id))}`\n \
If you wanna rename yourself, please use `!rename Your-new-in-game-name.` \n \
If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)")
        return

    id_accounts[ctx.author.id] = player_name

    with open(ACCOUNTS, 'w') as facc:
        json.dump(id_accounts, facc)

    # Must also add the player to the players db
    players_details: List[Dict[str, Any]] = []
    with open(PLAYERS_DETAILS) as pfile:
        players_details = json.load(pfile)

    new_player: Dict[str, Any] = {
        "id": 1 if not players_details else int(players_details[-1]["id"]) + 1,
        "name": player_name,
        "maps_played": [],
        "top10s": 0,
        "top1s": 0,
        "total_misses": 0,
        "perfects_percent_avg": 0,
        "total_score": 0,
    }
    players_details.append(new_player)

    with open(PLAYERS_DETAILS, 'w') as pfile:
        json.dump(players_details, pfile)


    for message in paginate("Ok, you're correctly registered :-)"):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='unregister', help='Unregister from everything (including your previous scores\n \
If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)')
@commands.before_invoke(record_usage)
async def unregister(ctx, confirm: str = ""):

    if confirm != "YEAHIMSURE!":
        await ctx.send(f"{ctx.author.name} didn't confirm, cancelling")
        return

    authorid: str = str(ctx.author.id)
    id_accounts: Dict[str,str] = load_accounts()
    player_name: str = id_accounts.get(authorid)
    print(authorid, player_name)
    if not player_name:
        await ctx.send('Player isnt registered in the first place (or didnt find him xD )')
        return

    print(f"Performing unregister of {ctx.author.name}'s account: {player_name}")

    # Deleting the player on custom songs's leaderboards
    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)

    for cs in custom_songs:
        rank_to_del: int = -1
        for rank, ldscore in enumerate(cs['leaderboard']):
            if ldscore['player_name'] == player_name:
                rank_to_del = rank
        if rank_to_del > -1:
            print(f"Oh, must delete the {rank_to_del}th element of {cs['full_name']} leaderboard")
            del(cs['leaderboard'][rank_to_del])
    print("Custom songs updated:", custom_songs)

    with open(CUSTOM_SONGS, 'w') as csfile:
        json.dump(custom_songs, csfile)

    with open(PLAYERS_DETAILS) as csfile:
        players_details = json.load(csfile)

    player_to_del: int = -1
    for pid, pdetails in enumerate(players_details):
        if pdetails['name'] == player_name:
            player_to_del = pid
    if player_to_del > -1:
        print(f"Oh, must delete the player at {player_to_del}th element")
        del(players_details[player_to_del])
    else:
        print("Player already deleted o.0")

    with open(PLAYERS_DETAILS, 'w') as csfile:
        json.dump(players_details, csfile)

    print("Players updated:", players_details)

    print(id_accounts)
    del(id_accounts[authorid])

    print("Accounts updated :", id_accounts)
    with open(ACCOUNTS, 'w') as facc:
        json.dump(id_accounts, facc)
    print("Accounts updated :", id_accounts)


    for message in paginate(f"Byee, no more scores from {player_name} :'("):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)


@bot.command(name='rename', help='Change your in-game name on all the leaderboards & stuff')
@commands.before_invoke(record_usage)
async def rename(ctx, new_name: str = ""):

    if not new_name:
        await ctx.send(f'Please specify the new name (with quotes if there are spaces). \n \
Exple: !rename "Awesome New Name"')
        return

    authorid: str = str(ctx.author.id)
    id_accounts: Dict[str,str] = load_accounts()
    player_name: str = id_accounts.get(authorid)
    print(authorid, player_name)
    if not player_name:
        await ctx.send('Player isnt registered (or didnt find him xD ), thus cant rename')
        return

    print(f"Renaming {ctx.author.name}'s account: {player_name} to {new_name}")

    # Renaming the player on custom songs's leaderboards
    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)

    for cs in custom_songs:
        for rank, ldscore in enumerate(cs['leaderboard']):
            if ldscore['player_name'] == player_name:
                print(f"Found the score of the player {ldscore}")
                ldscore['player_name'] = new_name

    print("Custom songs updated:", custom_songs)

    with open(CUSTOM_SONGS, 'w') as csfile:
        json.dump(custom_songs, csfile)

    with open(PLAYERS_DETAILS) as csfile:
        players_details = json.load(csfile)

    for pdetails in players_details:
        if pdetails['name'] == player_name:
            pdetails['name'] = new_name

    with open(PLAYERS_DETAILS, 'w') as csfile:
        json.dump(players_details, csfile)

    print("Players updated:", players_details)

    id_accounts[authorid] = new_name

    print("Accounts updated :", id_accounts)
    with open(ACCOUNTS, 'w') as facc:
        json.dump(id_accounts, facc)
    print("Accounts updated :", id_accounts)


    for message in paginate(f"Byee {player_name} and welcome {new_name} :-)"):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)


@bot.command(name='playerstats', help='Get overall stats of a player')
@commands.before_invoke(record_usage)
async def playerstats(ctx, player_name: str = ""):

    for message in paginate("Not Implemented Yet"):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='listmaps', help='List all maps')
@commands.before_invoke(record_usage)
async def list_maps(ctx):
    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)


    sorted_cs = sorted(custom_songs, key=lambda k: k['full_name'])

    all_maps: str = ""
    for cs in sorted_cs:
        all_maps += f"{cs['full_name']} \n"

    for message in paginate(all_maps):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='submit', help='Submit a new score with all the details. \n \
!submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
Exple: !submit https://image-or-video-proof.rocks Vodka Korpiklaani Vred 5 7777 1 99 3')
@commands.before_invoke(record_usage)
async def submit(
        ctx,
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

    print("Validating args")
    author = str(ctx.author.id)
    id_accounts = load_accounts()

    player_name = id_accounts.get(author)

    if not player_name:
        await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
Exple : `!register "OMDN | Gneuh [knee-uh]"`')
        return

    if not proof or not map_name or not band or not mapper or not difficulty or not score or not misses or not perfects_percent or not triggers:
        await ctx.send("Please fill all the field so admins can verify your submission easily :-). \n \
Your submission should look like : !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
For example : !submit https://image-or-video-proof.rocks Vodka Korpiklaani Vred 5 7777 1 99 3")
        return

    pendings: List[Dict[str, Any]] = []
    with open(PENDING_SCORES) as pfile:
        pendings = json.load(pfile)

    submission: Dict[str, Any] = {
        "map_name": map_name,
        "band": band,
        "mapper": mapper,
        "difficulty": difficulty,
        "player_name": player_name,
        "player_discord_id": ctx.author.id,
        "player_discord_name": ctx.author.name,
        "score": score,
        "misses": misses,
        "perfects_percent": perfects_percent,
        "triggers": triggers,
        "proof": proof
    }

    pendings.append(submission)

    with open(PENDING_SCORES, 'w') as pfile:
        json.dump(pendings, pfile)

    await ctx.send("Your request is correctly submitted. Please wait for an admin to verify your submission")


@bot.command(name='listplayers', help='List all players')
@commands.has_role(ROLE_ADMIN)
@commands.before_invoke(record_usage)
async def list_players(ctx):

    players_details: List[Dict[str, Any]] = []
    with open(PLAYERS_DETAILS) as pfile:
        players_details = json.load(pfile)

    all_players: str = ""

    for pdetails in players_details:
        print(pdetails)
        print(all_players)
        all_players += f"{pdetails['name']}\n"

    for message in paginate(all_players):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='listpending', help='List pending scores')
@commands.has_role(ROLE_ADMIN)
@commands.before_invoke(record_usage)
async def list_pending(ctx):

    pendings: List[Dict[str, Any]] = []
    with open(PENDING_SCORES) as pfile:
        pendings = json.load(pfile)

    if not pendings:
        await ctx.send("Looks like there isn't any pending submission, you're good to go :+1:")
        return

    output: str = ""

    for id_req, pdetails in enumerate(pendings):
        pdetails_str: str = ' '.join(['        ' + str(key) + ': ' + str(value) + '\n' for key, value in pdetails.items()])
        print(pdetails_str)
        output = f"{id_req + 1} :\n{pdetails_str}\n"
        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

@bot.command(name='valid', help='Validate a pending submission with the number of the pending score (the number seen on `!listpending`). Exple : `!valid 1`')
@commands.has_role(ROLE_ADMIN)
@commands.before_invoke(record_usage)
async def valid(ctx, id_pending: int = 0):

    if id_pending <= 0:
        await ctx.send("Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!valid 23`")
        return

    pendings: List[Dict[str, Any]] = []
    with open(PENDING_SCORES) as pfile:
        pendings = json.load(pfile)

    valid_score: Dict[str, Any] = {}
    for id_req, pdetails in enumerate(pendings):
        if id_req + 1 == id_pending:
            valid_score = pdetails

    if not valid_score:
        await ctx.send(f"Hmm, the pending submission {id_pending} was not found...(O.o)")
        return

    print("Valid score found:", valid_score)
    
    # Update leaderboards on custom_songs
    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)

    full_name: str = f"{valid_score['band']} - {valid_score['map_name']} - {valid_score['mapper']} - Level {valid_score['difficulty']}"
    print("Map to find : ", full_name)
    song_to_update: Dict[str, Any] = {}
    id_song: int = 0
    for idsong, cs in enumerate(custom_songs):
        if full_name == cs['full_name']:
            song_to_update = cs
            id_song = idsong

    if not song_to_update:
        await ctx.send(f"Hmm, looks like the map doesn't exist, please add it with `!newmap` before accepting a score on it :)")
        #TODO: Ask user if we should add the map automatically
        return

    print("Song to update found:", id_song, song_to_update)

    del(custom_songs[id_song])

    map_ld: List[Dict[str, Any]] = song_to_update["leaderboard"]
    print("Ld to update:", map_ld)
    # If player already in score, replace the score if better
    # + Find where the score should be placed
    new_rank: int = -1
    old_score: int = -1
    for rank, ld_score in enumerate(map_ld):
        if ld_score['player_name'] == valid_score['player_name']:
            if int(ld_score['score']) > int(valid_score['score']):
                await ctx.send(f"The player {valid_score['player_name']} has already a better score than the one submitted on {full_name}")
                return
            old_score = rank
        elif int(ld_score['score']) < int(valid_score['score']):
            new_rank = rank

    print("Old score placement (-1 if there isnt'):", old_score)
    if old_score > -1:
        del(map_ld[old_score])

    print("New score placement (-1 if there isnt'):", new_rank)
    if new_rank > -1:
        map_ld.insert(new_rank,valid_score)
    else:
        map_ld.append(valid_score)

    print("Leaderboard updated:", map_ld)
    song_to_update["leaderboard"] = map_ld
    print("Map updated:", song_to_update)
    if id_song < len(custom_songs):
        custom_songs[id_song] = song_to_update
    else:
        custom_songs.append(song_to_update)
    print("Custom songs updated:", custom_songs)

    with open(CUSTOM_SONGS, 'w') as csfile:
        json.dump(custom_songs, csfile)

    #Update player details
    #players_details: List[Dict[str, Any]] = []
    #with open(PLAYERS_DETAILS) as pfile:
    #    players_details = json.load(pfile)

    #for pdetails in players_details:
    #    if pdetails['name'] == valid_score['player_name']:
    #        #TODO: Also remove old scores stats...
    #        pdetails['total_score'] += int(valid_score['score'])
    #        pdetails['total_misses'] += int(valid_score['misses'])
    #        pdetails['maps_played'].append(song_to_update['id'])
    #        #TODO: Tops must be updated on all players... OMG !
    #        if new_rank + 1 <= 10:
    #            pdetails['top10s'] += 1
    #        if new_rank + 1 == 1:
    #            pdetails['top1s'] += 1
    #        #TODO: perfects_percent_avg must also be updated

    #with open(PLAYERS_DETAILS, 'w') as pfile:
    #    json.dump(players_details, pfile)

    print(f"Deleting pending {pendings[id_pending-1]}")
    # Remove score from pendings
    del(pendings[id_pending-1])
    with open(PENDING_SCORES, 'w') as pfile:
        json.dump(pendings, pfile)


    output: str = "Score is correctly saved and leaderboards are correctly updated."
    for message in paginate(output):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='deny', help='Deny a pending submission with the number of the pending score (the number seen on `!listpending`). `!deny pending_number reason`, exple : `!deny 1 "Incorrect map name"`')
@commands.has_role(ROLE_ADMIN)
@commands.before_invoke(record_usage)
async def deny(ctx, id_pending: int = 0, reason: str = ""):

    if id_pending <= 0:
        await ctx.send('Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!deny 23 "reason of denial"`')
        return

    pendings: List[Dict[str, Any]] = []
    with open(PENDING_SCORES) as pfile:
        pendings = json.load(pfile)

    denied_score: Dict[str, Any] = {}

    for id_req, pdetails in enumerate(pendings):
        if id_req + 1 == id_pending:
            denied_score = pdetails

    if not denied_score:
        await ctx.send(f"Hmm, the pending submission {id_pending} was not found...(O.o)")
        return

    del(pendings[id_pending-1])

    with open(PENDING_SCORES, 'w') as pfile:
        json.dump(pendings, pfile)
    
    output: str = f"Submission {denied_score} has been denied by {ctx.author} because {reason}"
    for message in paginate(output):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

@bot.command(name='newmap', help='Add a new custom map that will have a leaderboard associated. \n \
The cmd should look like : !newmap map_name band mapper difficulty\n \
For example : !newmap "System of a Down" "Genocidal Humanoidz" Skeelie 9\n \
(yeah, add quote if there are spaces)')
@commands.has_role(ROLE_ADMIN)
@commands.before_invoke(record_usage)
async def newmap(ctx, map_name: str = "", band: str = "", mapper: str = "", difficulty: str = ""):

    if not map_name or not band or not mapper:
        await ctx.send('Please, specify all the details of the new map. The cmd should look like : !newmap map_name band mapper difficulty\n \
For example : !newmap "Genocidal Humanoidz" "System of a Down" Skeelie 9\n \
(yeah, add quote if there are spaces)')
        return

    custom_songs: List[Dict[str, Any]] = []
    with open(CUSTOM_SONGS) as csfile:
        custom_songs = json.load(csfile)

    full_name: str = f"{band} - {map_name} - {mapper} - Level {difficulty}"

    higher_id: int = 0
    for cs in custom_songs:
        if cs['full_name'] == full_name:
            await ctx.send('Owah sorry, this map already exists :o \n \
                    If this is a new version, either remove the previous one with `!removemap` or add a version to the name or something but it can get messy xD')
            return
        if higher_id < cs['id']:
            higher_id = cs['id']

    new_map: Dict[str, Any] = {
        "id": higher_id + 1,
        "full_name": full_name,
        "name": map_name,
        "band": band,
        "mapper": mapper,
        "difficulty": difficulty,
        "leaderboard": []
    }

    custom_songs.append(new_map)
    with open(CUSTOM_SONGS, 'w') as csfile:
        json.dump(custom_songs, csfile)

    output: str = f"The map {full_name} is correctly added :-)"
    for message in paginate(output):
        msg_to_send = ''.join(message)
        await ctx.send(msg_to_send)

bot.run(TOKEN)

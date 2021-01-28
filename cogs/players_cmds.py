import json
import discord
from discord.ext import commands

from storage.db_layer import *

#TODO: Migrate top, topmap, playerstats, submit, listmaps searchmap
#TODO: Add 'cancel' to cancel a submission
#TODO: utils func to check parameter entered by players (especially on submissions)
#TODO: Maybe check if submission already exists..

class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='top', help='Shows the current top10 overall')
    @commands.before_invoke(record_usage)
    async def top(self, ctx, nb_to_show: int = 10):
    
        for message in paginate("Not totally implemented Yet (only checks total score over all maps for now)"):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
        print("Force update all players before showing top")

        players_details: List[Dict[str, Any]] = []
        with open(PLAYERS_DETAILS) as pfile:
            players_details = json.load(pfile)
        for pdetails in players_details:
            await self.playerstats(ctx, pdetails['name'], False)
    
        print("Ok, starting to get overall leaderboard")

        top_players: str = "\n"
    
        with open(PLAYERS_DETAILS) as pfile:
            players_details = json.load(pfile)

        if len(players_details) <= nb_to_show:
            nb_to_show = len(players_details)
    
        print("Nb players to show:", nb_to_show)

        sorted_players = sorted(players_details, key=lambda k: float(k['total_score']), reverse=True)
        
        for rank, pdetails in enumerate(sorted_players):
            if nb_to_show <= 0:
                break
            print(rank, pdetails)
            top_players += f"{str(rank+1)} - {pdetails['name']} : {pdetails['total_score']:.2f}\n"
            nb_to_show -= 1
    
        for message in paginate(top_players):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='topmap', help='Shows the current top on a specific map')
    @commands.before_invoke(record_usage)
    async def top_map(self, ctx, map_name: str = "", nb_to_show: int = 10):

        if not map_name:
            await ctx.send('Please, specify at least a word (will try to find corresponding maps loosely) or an uuid :-) ')
            return

        print("Starting to get map leaderboard")
    
        custom_songs: List[Dict[str, Any]] = []
        with open(CUSTOM_SONGS) as csfile:
            custom_songs = json.load(csfile)
    
        matching_songs: List[Dict[str, Any]] = []
        for cs in custom_songs:
            if map_name.lower() in cs['full_name'].lower():
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
    
    @commands.command(name='register', help='Register your in-game name (will be used to validate your proofs)')
    @commands.before_invoke(record_usage)
    async def register(self, ctx, player_name: str = ""):
    
        if not player_name:
            await ctx.send('Please indicate your in-game name. Exple : `!register "OMDN | Gneuh [knee-uh]"` (yeah, use quote if there are spaces & stuff !)')
            return
    
        if get_account_by_discord_id(ctx.author.id):
            await ctx.send(f"Uh? Looks like you're already registered as `{id_accounts.get(str(ctx.author.id))}`\n \
    If you wanna rename yourself, please use `!rename Your-new-in-game-name.` \n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)")
            return
    
        # Must also add the player to the players db
        id_player = get_last_index_from_index_sequence()

        # We set id_player == maps_played_id for simplicity
        # It's not mandatory but easier to think of

        # We also add player's details
        account: Dict[str, Any] = {
            "discord_id": str(ctx.author.id),
            "discord_name": ctx.author.name,
            "player_id": id_player,
            "player_name": player_name,
            "total_misses": 0,
            "perfects_percent_avg": 0,
            "total_score": 0,
            "total_triggers": 0,
        }
        add_account(account)
    
        for message in paginate("Ok, you're correctly registered :-)"):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='unregister', help='Unregister from everything (including your previous scores\n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)')
    @commands.before_invoke(record_usage)
    async def unregister(self, ctx, confirm: str = ""):
    
        if confirm != "YEAHIMSURE!":
            await ctx.send(f"{ctx.author.name} didn't confirm, cancelling")
            return
    
        account = get_account_by_discord_id(ctx.author.id)
        
        print(ctx.author.id, account)
        if not account:
            await ctx.send('Player isnt registered in the first place (or didnt find ? xD )')
            return
    
        player_name: str = account['player_name']
        print(f"Performing unregister of {ctx.author.name}'s account: {player_name}")

        delete_scores_on_lboard_by_player_id(account['player_id'])
        delete_account(account['player_id'])

        for message in paginate(f"Byee, no more scores from {player_name} :'("):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    
    @commands.command(name='rename', help='Change your in-game name on all the leaderboards & stuff')
    @commands.before_invoke(record_usage)
    async def rename(self, ctx, new_name: str = ""):
    
        if not new_name:
            await ctx.send(f'Please specify the new name (with quotes if there are spaces). \n \
    Exple: !rename "Awesome New Name"')
            return
    
        account = get_account_by_discord_id(ctx.author.id)
        
        print(ctx.author.id, account)
        if not account:
            await ctx.send('Player isnt registered (or didnt find him xD ), thus cant rename')
            return
    
        player_name: str = account['player_name']
        print(f"Renaming {ctx.author.name}'s account: {player_name} to {new_name}")

        player_id = account['player_id']
        update_account_by_player_id(player_id, 'player_name', new_name)
    
        for message in paginate(f"Byee {player_name} and welcome {new_name} :-)"):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    
    @commands.command(name='playerstats', help='Get overall stats of a player')
    @commands.before_invoke(record_usage)
    async def playerstats(self, ctx, player_name: str = "", called_as_cmd: bool = True):
    
        if called_as_cmd:
            for message in paginate("Not totally implemented Yet"):
                msg_to_send = ''.join(message)
                await ctx.send(msg_to_send)
    
        print("Starting to get player stats")

        if not player_name:
            print("Player name not in parameter. We look for the author of the message")
            id_accounts = load_accounts()
            player_name = id_accounts.get(str(ctx.author.id))
            print(f"Ok, the author is registered as {player_name}")
    
        if not player_name:
            await ctx.send('Player not registered and no player name chosen. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
or simply choose someone, for example : `!playerstats "OMDN | Gneuh [knee-uh]"`')
            return
    
        players_details: List[Dict[str, Any]] = []
        with open(PLAYERS_DETAILS) as pfile:
            players_details = json.load(pfile)

        pstats_str: str = ""
        total_score: float = 0
        total_misses: int = 0
        perfects_percent: float = 0
        perfects_percent_avg: float = 0
        total_triggers: int = 0
        for pdetails in players_details:
            if pdetails['name'] == player_name:
                print(f"{player_name} found")
                # Updating 
                #TODO: Also update top1s & top10s
                if not pdetails['maps_played']:
                    print(f"No scores found for {pdetails}")
                    pstats_str = f"No scores found for {player_name}"
                    break
                for mapp in pdetails['maps_played']:
                    total_score += float(mapp["score"])
                    total_misses += int(mapp["misses"])
                    perfects_percent += float(mapp["perfects_percent"])
                    total_triggers += int(mapp["triggers"])
                pdetails["total_score"] = total_score
                pdetails["total_misses"] = total_misses
                perfects_percent_avg = perfects_percent / len(pdetails['maps_played'])
                pdetails["perfects_percent_avg"] = perfects_percent_avg
                pdetails["total_triggers"] = total_triggers
                pstats_str =  f'{player_name}\n\t \
Total score: {total_score},\n\t \
Total misses: {total_misses},\n\t \
Total triggers: {total_triggers},\n\t \
Perfects percent average: {perfects_percent_avg}'
                print(pstats_str)
    
        if not pstats_str:
            await ctx.send(f'Hmmm, **{player_name}** not found :thinking:  Am I bugged? :upside_down: Or are you? xD')
            return
        
        with open(PLAYERS_DETAILS, 'w') as csfile:
            json.dump(players_details, csfile)
    
        print("Player updated:", player_name)

    
        if called_as_cmd:
            for message in paginate(pstats_str):
                msg_to_send = ''.join(message)
                await ctx.send(msg_to_send)
        
    
    @commands.command(name='listmaps', help='List all maps')
    @commands.before_invoke(record_usage)
    async def list_maps(self, ctx):
        await ctx.send("All maps 'scorable' are now from https://ragnasong.com ;-) \n \
You can use !searchmap to find exactly what you need to copy/paste for !submit")

    @commands.command(name='searchmap', help='Search for a specific map by pattern')
    @commands.before_invoke(record_usage)
    async def search_map(self, ctx, pattern: str = ""):

        if not pattern:
            await ctx.send("Please, specify a word to search for, or a uuid (hash). For example: !searchmap skeelie")
            return

        maps_found = search_map_by_pattern(pattern)

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

        if not output:
            await ctx.send(f"Sorry, couldn't find any map matching {pattern}")
            return

        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='submit', help='Submit a new score with all the details. \n \
    !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
    Exple: `!submit https://image-or-video-proof.rocks Vodka Korpiklaani Vred 6 7777 1 99 3`')
    @commands.before_invoke(record_usage)
    async def submit(
            self,
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
        account = get_account_by_discord_id(ctx.author.id)
        if not account:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return
    
        if not proof or not map_name or not band or not mapper or not difficulty or not score or not misses or not perfects_percent or not triggers:
            await ctx.send("Please fill all the field so admins can verify your submission easily :-). \n \
    Your submission should look like : !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
    For example : `!submit https://image-or-video-proof.rocks Vodka Korpiklaani Vred 5 7777 1 99 3`")
            return

        try:
            try_d = int(difficulty)
            if try_d < 1 or try_d > 20:
                raise ValueError
        except ValueError:
            await ctx.send("Difficulty should be a number between 1 and...20? ;-)")
            return

        try:
            try_d = float(score)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Score should be a number (can be decimal) and be positive ;-)")
            return

        try:
            try_d = int(misses)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Misses should be a number and be positive ;-)")
            return

        try:
            try_d = int(triggers)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Triggers should be a number and be positive ;-)")
            return

        try:
            try_d = float(perfects_percent)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Perfects percentage should be a number (can be decimal) and be positive ;-)")
            return
    
        map_submitted = list(search_map_by_title_artist_mapper(map_name, band, mapper))
        if not map_submitted:
            await ctx.send("Sorry, not maps were found with those artist/title/mapper. Please try to search your map with `!searchmap 'anything'` before submitting")
            return

        if len(map_submitted) > 1:
            await ctx.send("Hmm, looks like there are multiple maps with those artist/title/mapper.  \n \
                    Please try to search your map with `!searchmap 'anything'` to submit with uuid instead")
            return

        map_submitted = map_submitted[0]

        # Is difficulty submitted really coherent?
        if str(difficulty) not in map_submitted['difficulty']:
            await ctx.send(f"Sorry, the map's difficulty you submitted doesn't exist. This map only have those : {map_submitted['difficulty']}") 
            return

        # We take this chance to update player_discord_name because
        # we may not have it already (or it could have changed)
        player_id = account['player_id']
        discord_name = ctx.author.name
        update_account_by_player_id(player_id, 'discord_name', discord_name)

        # Ok submission seems valid from the backend point of view
        # We push it to admins to verify the proof 
        # (can't identify anything on an image or video for now xD )
        submission: Dict[str, Any] = {}
        submission['map_uuid'] = map_submitted['uuid']
        submission['player_id'] = player_id
        submission['difficulty_played'] = difficulty
        submission['score'] = score
        submission['misses'] = misses
        submission['perfects_percent'] = perfects_percent
        submission['triggers'] = triggers
        submission['proof'] = proof

        add_pending_submission(submission)
    
        await ctx.send("Your request is correctly submitted. Please wait for an admin to verify your submission")

    @commands.command(name='submit', help='Submit a new score with uuid. \n \
    !submit proof uuid difficulty score misses perfects_percent triggers \n \
    Exple: `!submit https://weblink/proof.png 46df5d714b99306e0a31d60970703733c72c3efc 6 7777 1 99 3`')
    @commands.before_invoke(record_usage)
    async def submit(
            self,
            ctx,
            proof: str = "",
            uuid: str = "",
            difficulty: str = "",
            score: str = "",
            misses: str = "",
            perfects_percent: str = "",
            triggers: str = "",
        ):
    
        print("Validating args")

        account = get_account_by_discord_id(ctx.author.id)
        if not account:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return
    
        if not proof or not uuid or not difficulty or not score or not misses or not perfects_percent or not triggers:
            await ctx.send("Please fill all the field so admins can verify your submission easily :-). \n \
    Your submission should look like : !submit proof uuid difficulty score misses perfects_percent triggers \n \
    For example : `!submit https://image-or-video-proof.rocks 46df5d714b99306e0a31d60970703733c72c3efc 5 7777 1 99 3`")
            return

        try:
            try_d = int(difficulty)
            if try_d < 1 or try_d > 20:
                raise ValueError
        except ValueError:
            await ctx.send("Difficulty should be a number between 1 and...20? ;-)")
            return

        try:
            try_d = float(score)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Score should be a number (can be decimal) and be positive ;-)")
            return

        try:
            try_d = int(misses)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Misses should be a number and be positive ;-)")
            return

        try:
            try_d = int(triggers)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Triggers should be a number and be positive ;-)")
            return

        try:
            try_d = float(perfects_percent)
            if try_d < 0:
                raise ValueError
        except ValueError:
            await ctx.send("Perfects percentage should be a number (can be decimal) and be positive ;-)")
            return

        map_submitted = get_map_by_uuid(uuid)
        if not map_submitted:
            await ctx.send("Sorry, not maps were found with this uuid. Please try to search your map with `!searchmap 'anything'`")
            return

        # Is difficulty submitted really coherent?
        if str(difficulty) not in map_submitted['difficulty']:
            await ctx.send(f"Sorry, the map's difficulty you submitted doesn't exist. This map only have those : {map_submitted['difficulty']}") 
            return

        # We take this chance to update player_discord_name because
        # we may not have it already (or it could have changed)
        player_id = account['player_id']
        discord_name = ctx.author.name
        update_account_by_player_id(player_id, 'discord_name', discord_name)

        # Ok submission seems valid from the backend point of view
        # We push it to admins to verify the proof 
        # (can't identify anything on an image or video for now xD )
        submission: Dict[str, Any] = {}
        submission['map_uuid'] = uuid
        submission['player_id'] = player_id
        submission['difficulty_played'] = difficulty
        submission['score'] = score
        submission['misses'] = misses
        submission['perfects_percent'] = perfects_percent
        submission['triggers'] = triggers
        submission['proof'] = proof

        add_pending_submission(submission)
    
        await ctx.send("Your request is correctly submitted. Please wait for an admin to verify your submission")

    @commands.command(name='mysubs', help='Get a list of your pending submissions if there are any')
    @commands.before_invoke(record_usage)
    async def my_submissions(self, ctx):
        account = get_account_by_discord_id(ctx.author.id)
        if not account:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return

        output: str = ""
        pendings =  get_pending_submissions_by_player_id(account['player_id'])

        for id_req, pdetails in enumerate(pendings):
            print(id_req, pdetails)
            map_submitted = get_map_by_uuid(pdetails['map_uuid'])
            print(map_submitted)
            account = get_account_by_player_id(pdetails['player_id'])
            print(account)
            pdetails_str: str = f"        In-game name: {account['player_name']}" + '\n'
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
            output = f"{id_req + 1} :     Discord user that submitted: {account['discord_name']}\n{pdetails_str}\n"
            for message in paginate(output):
                msg_to_send = ''.join(message)
                await ctx.send(msg_to_send)

        if not output:
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

    @commands.command(name='cancelsub', help='Cancel one of your pending submissions by submission id (shown with `!mysubs`) \n \
For example : `!cancelsub 2`')
    @commands.before_invoke(record_usage)
    async def cancel_submission(self, ctx, id_submission: int = -1):

        if id_submission < 1:
            await ctx.send("Please indicate the number of the submission indicated on `!mysubs`")
            return


        account = get_account_by_discord_id(ctx.author.id)
        if not account:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return

        output: str = ""
        pendings =  list(get_pending_submissions_by_player_id(account['player_id']))
        if not pendings:
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

        try:
            try_d = int(id_submission)
            if try_d > len(pendings):
                raise ValueError
        except ValueError:
            await ctx.send("The submission id should be a number and between 1 and the number of pending submissions you have ;-)")
            return

        psub_to_cancel = pendings[id_submission - 1]

        print("Sub to cancel", psub_to_cancel)
        delete_pending_submission(psub_to_cancel)

        await ctx.send(f"The submission `{psub_to_cancel}` is now cancelled")


def setup(bot):
    bot.add_cog(Players(bot))

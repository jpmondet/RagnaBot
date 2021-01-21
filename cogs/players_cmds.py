import json
import discord
from discord.ext import commands

from utils.bot_utils import *


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
            "total_triggers": 0,
        }
        players_details.append(new_player)
    
        with open(PLAYERS_DETAILS, 'w') as pfile:
            json.dump(players_details, pfile)
    
    
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
    
    
    @commands.command(name='rename', help='Change your in-game name on all the leaderboards & stuff')
    @commands.before_invoke(record_usage)
    async def rename(self, ctx, new_name: str = ""):
    
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
        print(ctx.author.id)
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


def setup(bot):
    bot.add_cog(Players(bot))

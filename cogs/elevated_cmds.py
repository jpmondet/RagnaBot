import json
import discord
from discord.ext import commands

from storage.db_layer import *

class Moderators(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='listplayers', help='List all players')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def list_players(self, ctx, page: int = 1, perpage: int = 10):

        # page 1 -> 1 to 10 players
        # page 2 -> 11 to 20 
        # page x -> perpage * (page - 1) + nb_player

        nb_min = perpage * (page - 1)
        nb_max = perpage * (page - 1) + (perpage + 1)

        all_players: str = ""
        for nb_player, acc in enumerate(get_accounts()):
            if nb_player + 1 <= nb_min:
                continue
            if nb_player + 1 >= nb_max:
                break
            if nb_player + 1 > nb_min and nb_player + 1 < nb_max:
                print(acc)
                all_players += f"{acc['player_name']}\n"

        for message in paginate(all_players):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='searchplayer', help='Search a player by name')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def search_players(self, ctx, name_to_find: str = ""):

        if not name_to_find:
            await ctx.send("Please specify a word to find. For exemple !searchplayer gneuh should find the player with \n \
this word in the name")
            return

        players_found = search_account_by_name(name_to_find)

        all_players = ""
        for acc in players_found:
            all_players += f"{acc['player_name']}\n"

        if not all_players:
            await ctx.send("No player found with that pattern, sorry")
            return

        for message in paginate(all_players):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='listpending', help='List pending scores')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def list_pending(self, ctx):

        pendings = get_pending_submissions()

        output: str = ""

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
            await ctx.send("Looks like there isn't any pending submission, you're good to go :+1:")
            return


    @commands.command(name='valid', help='Validate a pending submission with the number of the pending score (the number seen on `!listpending`). Exple : `!valid 1`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def valid(self, ctx, id_pending: int = 0):

        if id_pending <= 0:
            await ctx.send("Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!valid 23`")
            return

        pendings = list(get_pending_submissions())
        if not pendings:
            await ctx.send("Looks like there isn't any pending submission right now")
            return

        if id_pending > len(pendings):
            await ctx.send(f"Please, indicate a pending id between 1 and {len(pendings)}")
            return

        valid_score: Dict[str, Any] = pendings[id_pending - 1]

        print("Valid score found:", valid_score)
        del(valid_score['_id'])

        delete_pending_submission(valid_score)

        # Check if a score already exists for this map & player
        old_score = get_score_by_player_id_map_uuid_diff(valid_score['player_id'], valid_score['map_uuid'], valid_score['difficulty'])
        if old_score:
            print(old_score)
            if score < float(old_score['score']):
                await ctx.send("Looks like the player already has a better score for this map/difficulty")
                return

        add_score_to_cslboard(valid_score)

        misses: int = int(valid_score['misses'])
        triggers: int = int(valid_score['triggers'])
        score: float = float(valid_score['total_score'])
        perfects_percent: float = float(valid_score['total_score'])

        if old_score:
            misses -= int(old_score['misses'])
            triggers -= int(old_score['triggers'])
            score -= float(old_score['total_score'])
            perfects_percent -= float(old_score['perfects_percent'])

        player_id: int = valid_score['player_id']
        account: Dict[str, Any] = get_account_by_player_id(player_id)

        total_misses: int = int(account['total_misses']) + misses
        total_triggers: int = int(account['total_triggers']) + triggers
        total_score: float = float(account['total_score']) + score
        perfects_percent_total: float = float(account['perfects_percent_total']) + perfects_percent

        update_account_by_player_id(player_id, 'total_misses', total_misses)
        update_account_by_player_id(player_id, 'total_triggers', total_triggers)
        update_account_by_player_id(player_id, 'total_score', total_score)
        update_account_by_player_id(player_id, 'perfects_percent_total', perfects_percent_total)

        output: str = "Score is correctly saved and leaderboards are correctly updated."
        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='deny', help='Deny a pending submission with the number of the pending score (the number seen on `!listpending`). `!deny pending_number reason`, exple : `!deny 1 "Incorrect map name"`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def deny(self, ctx, id_pending: int = 0, reason: str = ""):

        if id_pending <= 0:
            await ctx.send("Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!valid 23`")
            return

        pendings = list(get_pending_submissions())
        if not pendings:
            await ctx.send("Looks like there isn't any pending submission right now")
            return

        if id_pending > len(pendings):
            await ctx.send(f"Please, indicate a pending id between 1 and {len(pendings)}")
            return

        denied_score: Dict[str, Any] = pendings[id_pending - 1]

        print("Score to deny found:", denied_score)
        del(denied_score['_id'])

        delete_pending_submission(denied_score)

        output: str = f"Submission {denied_score} has been denied by {ctx.author} because: {reason}"
        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)


def setup(bot):
    bot.add_cog(Moderators(bot))

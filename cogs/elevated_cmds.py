import json
import discord
from discord.ext import commands

from storage.db_layer import *
import compute.middle_layer as cml
from utils.bot_utils import paginate, record_usage, check_if_registered
from utils.env import ROLE_ADMIN

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
        for nb_player, acc in enumerate(cml.search_accounts_by_pattern("")):
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

    @commands.command(name='listpending', help='List pending scores')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def list_pending(self, ctx):

        output: str = cml.get_pending_subs_player()

        if isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission, you're good to go :+1: ")
            return

        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='valid', help='Validate a pending submission with the number of the pending score (the number seen on `!listpending`). Exple : `!valid 1`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def valid(self, ctx, id_pending: int = 0):
        for message in paginate(cml.validate_submission(id_pending)):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='deny', help='Deny a pending submission with the number of the pending score (the number seen on `!listpending`). `!deny pending_number reason`, exple : `!deny 1 "Incorrect map name"`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def deny(self, ctx, id_pending: int = -1, reason: str = ""):

        if id_pending <= 0:
            await ctx.send("Please, indicate the id of the pending score to validate (shown with `!listpending`). For example : `!deny 23`")
            return

        output: str = cml.cancel_submission_of_player(0, id_pending)
        if isinstance(output, int):
            await ctx.send("The submission id should be a number and between 1 and the number of pending submissions you have ;-)")
            return
        elif isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission")
            return

        output: str = f"Submission {output} has been denied by {ctx.author} because: {reason}"
        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='force-update-maps', help='Polls the Ragnasong.com API to update maps list') 
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def force_update_maps(self, ctx):
        maps_added: str = cml.force_update_maps()
        for message in paginate(maps_added):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)


def setup(bot):
    bot.add_cog(Moderators(bot))

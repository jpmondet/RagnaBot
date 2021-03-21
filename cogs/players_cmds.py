import json
import discord
from discord.ext import commands

import compute.middle_layer as cml
from utils.bot_utils import paginate, record_usage, check_if_registered


class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="top", help="Shows the current top10 overall")
    @commands.before_invoke(record_usage)
    async def top(self, ctx, nb_to_show: int = 10):
        for message in paginate(cml.get_top_players(nb_to_show)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(name="topmap", help="Shows the current top on a specific map")
    @commands.before_invoke(record_usage)
    async def top_map(self, ctx, map_name: str = "", nb_to_show: int = 10):
        for message in paginate(cml.get_top_players_on_specific_map(map_name, nb_to_show)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="register", help="Register your in-game name (will be used to validate your proofs)"
    )
    @commands.before_invoke(record_usage)
    async def register(self, ctx, player_name: str = ""):
        for message in paginate(
            cml.registering_player(ctx.author.id, ctx.author.name, player_name)
        ):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="unregister",
        help="Unregister from everything (including your previous scores\n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)",
    )
    @commands.check(check_if_registered)
    @commands.before_invoke(record_usage)
    async def unregister(self, ctx, confirm: str = ""):
        for message in paginate(cml.unregistering_player(ctx.author.id, ctx.author.name, confirm)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="rename", help="Change your in-game name on all the leaderboards & stuff"
    )
    @commands.check(check_if_registered)
    @commands.before_invoke(record_usage)
    async def rename(self, ctx, new_name: str = ""):
        for message in paginate(cml.rename_player(ctx.author.id, new_name)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(name="playerstats", help="Get overall stats of a player")
    @commands.before_invoke(record_usage)
    async def playerstats(self, ctx, player_name: str = ""):
        for message in paginate(cml.get_player_stats(ctx.author.id, player_name)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(name="searchplayer", help="Search a player by name")
    @commands.before_invoke(record_usage)
    async def search_players(self, ctx, name_to_find: str = ""):
        for message in paginate(cml.search_players_names_by_name_pattern(name_to_find)):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(name="listmaps", help="List all maps")
    @commands.before_invoke(record_usage)
    async def list_maps(self, ctx):

        await ctx.send(
            "All maps 'scorable' are now from https://ragnasong.com ;-) \n \
You can use !searchmap to find exactly what you need to copy/paste for !submit"
        )

    @commands.command(name="searchmap", help="Search for a specific map by pattern")
    @commands.before_invoke(record_usage)
    async def search_map(self, ctx, pattern: str = ""):

        if not pattern:
            await ctx.send(
                "Please, specify a word to search for, or a uuid (hash). For example: !searchmap skeelie"
            )
            return

        output = cml.get_formatted_maps_by_pattern(pattern)
        if not output:
            await ctx.send(f"Sorry, couldn't find any map matching {pattern}")
            return

        for message in paginate(output):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="submit-by-map-name",
        help="Submit a new score with all the details. \n \
    !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
    Exple: `!submit-by-map-name https://image-or-video-proof.rocks Vodka Korpiklaani Vred 6 7777 1 99 3`",
    )
    @commands.before_invoke(record_usage)
    @commands.check(check_if_registered)
    async def submit_by_map_name(
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
        for message in paginate(
            cml.handle_player_submission(
                ctx.author.id,
                ctx.author.name,
                proof,
                difficulty,
                score,
                misses,
                perfects_percent,
                triggers,
                map_name,
                band,
                mapper,
            )
        ):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="submit",
        help="Submit a new score with uuid. \n \
    !submit proof uuid difficulty score misses perfects_percent triggers \n \
    Exple: `!submit https://weblink/proof.png 46df5d714b99306e0a31d60970703733c72c3efc 6 7777 1 99 3`",
    )
    @commands.before_invoke(record_usage)
    @commands.check(check_if_registered)
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
        for message in paginate(
            cml.handle_player_submission(
                ctx.author.id,
                ctx.author.name,
                proof,
                difficulty,
                score,
                misses,
                perfects_percent,
                triggers,
                "",
                "",
                "",
                uuid,
            )
        ):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(name="mysubs", help="Get a list of your pending submissions if there are any")
    @commands.before_invoke(record_usage)
    @commands.check(check_if_registered)
    async def my_submissions(self, ctx):

        output: str = cml.get_pending_subs_player(ctx.author.id)

        if isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

        for message in paginate(output):
            msg_to_send = "".join(message)
            await ctx.send(msg_to_send)

    @commands.command(
        name="cancelsub",
        help="Cancel one of your pending submissions by submission id (shown with `!mysubs`) \n \
For example : `!cancelsub 2`",
    )
    @commands.before_invoke(record_usage)
    @commands.check(check_if_registered)
    async def cancel_submission(self, ctx, id_submission: int = -1):

        if id_submission < 1:
            await ctx.send("Please indicate the number of the submission indicated on `!mysubs`")
            return

        output: str = cml.cancel_submission_of_player(ctx.author.id, id_submission)
        if isinstance(output, int):
            await ctx.send(
                "The submission id should be a number and between 1 and the number of pending submissions you have ;-)"
            )
            return
        elif isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

        await ctx.send(f"The submission `{output}` is now cancelled")


def setup(bot):
    bot.add_cog(Players(bot))

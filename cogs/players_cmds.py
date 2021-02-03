import json
import discord
from discord.ext import commands

import compute.middle_layer as cml
from utils.bot_utils import paginate, record_usage, send_not_registered_message

#TODO: utils func to check parameter entered by players (especially on submissions)

class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='top', help='Shows the current top10 overall')
    @commands.before_invoke(record_usage)
    async def top(self, ctx, nb_to_show: int = 10):
        for message in paginate(cml.get_top_players(nb_to_show)):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='topmap', help='Shows the current top on a specific map')
    @commands.before_invoke(record_usage)
    async def top_map(self, ctx, map_name: str = "", nb_to_show: int = 10):

        if not map_name:
            await ctx.send('Please, specify at least a word (will try to find corresponding maps loosely) or an uuid :-) ')
            return

        print("Starting to get map leaderboard")

        leaders: str, nb_songs: int = cml.get_top_players_on_specific_map(map_name, nb_to_show)

        if not nb_songs:
            await ctx.send('Sorry, no maps were found with this pattern')
            return

        if nb_songs > 1:
            await ctx.send('We found more than 1 maps with your pattern, showing only the first')
    
        for message in paginate(leaders):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='register', help='Register your in-game name (will be used to validate your proofs)')
    @commands.before_invoke(record_usage)
    async def register(self, ctx, player_name: str = ""):
    
        if not player_name:
            await ctx.send('Please indicate your in-game name. Exple : `!register "OMDN | Gneuh [knee-uh]"` (yeah, use quote if there are spaces & stuff !)')
            return
    
        already_registered: str = cml.registering_player(ctx.author.id, ctx.author.name, player_name)
        if already_registered:
            await ctx.send(f"Uh? Looks like you're already registered as `{already_registered}`\n \
    If you wanna rename yourself, please use `!rename Your-new-in-game-name.` \n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)")
            return
    
        for message in paginate("Ok, you're correctly registered :-)"):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='unregister', help='Unregister from everything (including your previous scores\n \
    If you wanna unregister, please use `!unregister YEAHIMSURE!` (but your scores will be deleted as well, be careful ! ^^)')
    @commands.before_invoke(record_usage)
    async def unregister(self, ctx, confirm: str = ""):
    
        if confirm != "YEAHIMSURE!":
            await ctx.send(f"{ctx.author.name} didn't confirm, cancelling (send `!unregister YEAHIMSURE!` to confirm)")
            return
    
        already_registered: str = cml.unregistering_player(ctx.author.id)
        if not already_registered:
            await ctx.send(f"Uh? Looks like you're not registered xD")
            return
        
        player_name = already_registered

        for message in paginate(f"Byee, no more scores from {player_name} :'("):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    
    @commands.command(name='rename', help='Change your in-game name on all the leaderboards & stuff')
    @commands.before_invoke(record_usage)
    async def rename(self, ctx, new_name: str = ""):
    
        if not new_name:
            await ctx.send(f'Please specify the new name (with quotes if there are spaces). \n \
    Exple: `!rename "Awesome New Name"`')
            return
    
        already_registered = cml.rename_player(ctx.author.id, new_name)
        if not already_registered:
            await ctx.send('Player isnt registered (or didnt find him xD ), thus cant rename')
            return

        player_name = already_registered
    
        for message in paginate(f"Byee {player_name} and welcome {new_name} :-)"):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    
    @commands.command(name='playerstats', help='Get overall stats of a player')
    @commands.before_invoke(record_usage)
    async def playerstats(self, ctx, player_name: str = ""):

        print("Starting to get player stats")

        str_returned = cml.get_player_stats(ctx.author.id, player_name)
        if not str_returned and not player_name:
            await ctx.send('Player not registered and no player name chosen. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n'
            return
        elif not str_returned and player_name:
            await ctx.send("No player found with that pattern, sorry")
            return
    
        for message in paginate(str_returned):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)

    @commands.command(name='searchplayer', help='Search a player by name')
    @commands.before_invoke(record_usage)
    async def search_players(self, ctx, name_to_find: str = ""):

        if not name_to_find:
            await ctx.send("Please specify a word to find. For exemple !searchplayer gneuh should find the player with \n \
this word in the name")
            return
        
        players_found = cml.search_players_names_by_name_pattern(name_to_find)

        if not players_found:
            await ctx.send("No player found with that pattern, sorry")
            return

        for message in paginate(players_found):
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

        output = cml.get_formatted_maps_by_pattern(pattern)
        if not output:
            await ctx.send(f"Sorry, couldn't find any map matching {pattern}")
            return

        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)
    
    @commands.command(name='submit-by-map-name', help='Submit a new score with all the details. \n \
    !submit proof map_name band mapper difficulty score misses perfects_percent triggers \n \
    Exple: `!submit https://image-or-video-proof.rocks Vodka Korpiklaani Vred 6 7777 1 99 3`')
    @commands.before_invoke(record_usage)
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
    
        print("Validating args")
        if not cml.check_if_registered(ctx.author.id):
            send_not_registered_message(ctx.send)
            return
        try:
            cml.handle_player_submission()
        except AttributeError as ae:
            await ctx.send(str(ae))
    
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

        output: str = cml.get_pending_subs_player(ctx.author.id)

        if isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

        if not output:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return

        for message in paginate(output):
            msg_to_send = ''.join(message)
            await ctx.send(msg_to_send)


    @commands.command(name='cancelsub', help='Cancel one of your pending submissions by submission id (shown with `!mysubs`) \n \
For example : `!cancelsub 2`')
    @commands.before_invoke(record_usage)
    async def cancel_submission(self, ctx, id_submission: int = -1):

        if id_submission < 1:
            await ctx.send("Please indicate the number of the submission indicated on `!mysubs`")
            return

        output: str = cml.cancel_submission_of_player(ctx.author.id, id_submission)
        if isinstance(output, int):
            await ctx.send("The submission id should be a number and between 1 and the number of pending submissions you have ;-)")
            return
        elif isinstance(output, list):
            await ctx.send("Looks like there isn't any pending submission for your account")
            return

        #else it's a string:
        if not output:
            await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
            return

        await ctx.send(f"The submission `{output}` is now cancelled")


def setup(bot):
    bot.add_cog(Players(bot))

import json
import discord
from discord.ext import commands

from utils.bot_utils import *


class Moderators(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='listplayers', help='List all players')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def list_players(self, ctx):

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

    @commands.command(name='listpending', help='List pending scores')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def list_pending(self, ctx):

        pendings: List[Dict[str, Any]] = []
        print(pendings)
        with open(PENDING_SCORES) as pfile:
            pendings = json.load(pfile)
        print(pendings)

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

    @commands.command(name='valid', help='Validate a pending submission with the number of the pending score (the number seen on `!listpending`). Exple : `!valid 1`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def valid(self, ctx, id_pending: int = 0):

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
            await ctx.send(f"Hmm, looks like the map **{full_name}** doesn't exist, please add it with `!newmap` before accepting a score on it :)")
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

    @commands.command(name='deny', help='Deny a pending submission with the number of the pending score (the number seen on `!listpending`). `!deny pending_number reason`, exple : `!deny 1 "Incorrect map name"`')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def deny(self, ctx, id_pending: int = 0, reason: str = ""):

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

    @commands.command(name='newmap', help='Add a new custom map that will have a leaderboard associated. \n \
    The cmd should look like : !newmap map_name band mapper difficulty\n \
    For example : !newmap "System of a Down" "Genocidal Humanoidz" Skeelie 9\n \
    (yeah, add quote if there are spaces)')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def newmap(self, ctx, map_name: str = "", band: str = "", mapper: str = "", difficulty: str = ""):

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
                await ctx.send(f'Owah sorry, the map **{full_name}** already exists :o \n \
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

    @commands.command(name='auto-add-maps', help='Automatically read the map-check channel to add new maps')
    @commands.has_any_role(*ROLE_ADMIN)
    @commands.before_invoke(record_usage)
    async def autoaddmaps(self, ctx, limit: int =10000):
        # Getting messages from the maps channel:
        fixed_channel = ctx.bot.get_channel(790326235615592458)
        async for msg in fixed_channel.history(limit=limit):
            #{'footer': {'text': 'How to download? (look at the chanel "tuto")'},
            #'image': {'url': 'https://i1.wp.com/www.pozzo-live.com/wp-content/uploads/2020/11/123987181_10158117518049032_1805713449174542166_o.jpg?ssl=1', 'proxy_url': 'https://images-ext-1.discordapp.net/external/diFTeaQxBlYCYHZKSFwo6hm4LVN0sLupYC9Vmt_iy3Y/%3Fssl%3D1/https/i1.wp.com/www.pozzo-live.com/wp-content/uploads/2020/11/123987181_10158117518049032_1805713449174542166_o.jpg',
            #    'width': 2048, 'height': 2048}, 'author': {'name': 'Difficulty : 5 & 7 & 10'}, 'color': 15662848, 'type': 'rich', i
            #'description': 'by Skeelie', 'url': 'https://cloud.ghosthub.fr/s/xRaojKCYbZ3ibBj', 'title': 'System Of A Down - Genocidal Humanoidz'}
            if msg.embeds:
                d_embed = msg.embeds[0].to_dict()
                if not isinstance(d_embed, dict):
                    # Must not be a map :
                    print(d_embed)
                    continue
                if not d_embed.get('title'):
                    # Sometimes, there are weird maps with some missing metadatas : 
                        #{'footer': {'text': 'How to download? (look at the chanel "tuto")'}, 'image': {'url': 'https://images.genius.com/97025d7ad6f33049688ada91b3a35368.1000x1000x1.jpg', 'proxy_url': 'https://images-ext-2.discordapp.net/external/2P8Z9cAbv6qZuCjWT8V-UxNES9SXHdZ6otHQQGuTM6M/https/images.genius.com/97025d7ad6f33049688ada91b3a35368.1000x1000x1.jpg', 'width': 1000, 'height': 1000}, 'author': {'name': 'AJR-Beats', 'url': 'https://cloud.ghosthub.fr/s/sbS3Hy9xf7638Za'}, 'color': 15662848, 'type': 'rich', 'description': 'by 4FriendZone'}
                    print(d_embed)
                    continue
                map_band_title = d_embed['title'].split('-')
                if len(map_band_title) < 2:
                    # Some maps have strange '–' instead of '-' as separator
                    map_band_title = d_embed['title'].split('–')
                map_band = map_band_title[0].strip()
                # In case there was a '-' in the name of the map, we join it back
                map_title = '-'.join(map_band_title[1:])
                map_title = map_title.strip()
                map_diffs = d_embed['author']['name'].split(':')[1].split('&')
                map_mapper = d_embed['description'].split('by')[1].strip()
                for diff in map_diffs:
                    print(map_band, map_title, map_mapper, diff.strip())
                    # Now that we have all infos, we actually add the maps
                    await self.newmap(ctx, map_title, map_band, map_mapper, diff.strip())


def setup(bot):
    bot.add_cog(Moderators(bot))

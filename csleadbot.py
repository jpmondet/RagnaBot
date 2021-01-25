""" Discord bot """

#! /usr/bin/env python3

import discord
from discord.ext import commands
from typing import Dict, List, Any

from storage.db_layer import *

CUSTOM_COGS = ["cogs.players_cmds", "cogs.elevated_cmds"]

if (
    not list(CUSTOM_SONGS_COLLECTION.find())
    or not list(LBOARDS_COLLECTION.find())
    or not list(ACCOUNTS_COLLECTION.find())
    or not list(PENDING_SCORES_COLLECTION.find())
):
    prep_db_if_not_exist()

# BOT FUNCTIONS START HERE
bot = commands.Bot(command_prefix=CMD_PREFIX)


@bot.check
def check_channel(ctx):
    if str(ctx.channel) in CHANNEL and str(ctx.guild) in GUILD:
        return True
    else:
        raise commands.errors.CheckFailure("channelerr")


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord and ready to get cmds")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send("Sorry, this command is not available in DMs.")
        return
    if isinstance(error, commands.errors.CheckFailure):
        if str(error) == "channelerr":
            print(
                f"[CHANNELERR] {ctx.author} asked for {ctx.message.content} on chan {ctx.channel} of {ctx.guild} at {ctx.message.created_at}"
            )
            return
        await ctx.send("Sorry, you do not have the correct role for this command.")
        return
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(
            "Sorry, we have to limit this command to 1 use every 60 seconds..."
        )
        return
    else:
        print(error)
        return


for cust_cog in CUSTOM_COGS:
    bot.load_extension(cust_cog)

bot.run(TOKEN, bot=True, reconnect=True)

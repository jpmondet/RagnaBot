""" Discord bot """

#! /usr/bin/env python3

import discord
from discord.ext import commands
from typing import Dict, List, Any

from compute.middle_layer import check_backend
from utils.env import TOKEN, CHANNEL, GUILD, CMD_PREFIX

CUSTOM_COGS = ["cogs.players_cmds", "cogs.elevated_cmds"]
        
NEED_REGISTER_FUNCS = {"submit-by-map-name", "submit", "unregister", "rename", "mysubs", "cancelsub"}

# BOT FUNCTIONS START HERE
BOT = commands.Bot(command_prefix=CMD_PREFIX)

@BOT.check
def check_channel(ctx):
    if str(ctx.channel) in CHANNEL and str(ctx.guild) in GUILD:
        return True
    else:
        raise commands.errors.CheckFailure("channelerr")


@BOT.event
async def on_ready():
    print(f"{BOT.user.name} has connected to Discord and ready to get cmds")


@BOT.event
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
        try:
            # Check if player is registered
            err_str = str(error)
            command_failed = err_str.split('command')[1].split('failed')[0].strip()
            print(str(error))
            print(err_str)
            print(command_failed)
            if command_failed in NEED_REGISTER_FUNCS:
                await ctx.send('Player not registered. Please use `!register "YOUR_INGAME_NAME"` (yeah, with **quotes** ^^) to register.\n \
    Exple : `!register "OMDN | Gneuh [knee-uh]"`')
                return
        except IndexError:
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

def start_bot() -> None:
    # Ensure that backend is coherent and up&running before anything
    if not check_backend():
        print("Hmm, backend is having issues. Is mongodb up? Stopping here")
        return

    for cust_cog in CUSTOM_COGS:
        BOT.load_extension(cust_cog)

    BOT.run(TOKEN, bot=True, reconnect=True)

if __name__ == "__main__":
    start_bot()

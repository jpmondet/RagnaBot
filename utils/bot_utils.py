""" Some utils used in all bot files """

#! /usr/bin/env python3

from os import getenv
from json import load as jload
from typing import Dict, List, Any

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = getenv("DISCORD_TOKEN")
GUILD: str = getenv('DISCORD_GUILD').split(',')
CHANNEL: str = getenv('DISCORD_CHANNEL').split(',')
ROLE_ADMIN: str = getenv('RAGNABOT_ROLE_ADMIN').split(',')
CMD_PREFIX: str = getenv("RAGNABOT_CMD_PREFIX")

CUSTOM_SONGS: str = "custom_songs.json"
PLAYERS_DETAILS: str = "players.json"
PENDING_SCORES: str = "pending_scores.json"
ACCOUNTS: str = "id_accounts_list.json"

def load_accounts():
    """ Loads registered discord ids accs from files and return the associated dict """
    id_accounts: Dict[str, str] = {}

    with open(ACCOUNTS, 'r') as facc:
        id_accounts = jload(facc)
    
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

async def record_usage(instance, ctx):
    print(f"[{instance}] {ctx.author} asked for {ctx.message.content} on chan {ctx.channel} of {ctx.guild} at {ctx.message.created_at}")

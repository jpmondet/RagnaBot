""" Some utils used in all bot files """

#! /usr/bin/env python3

from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN: str = getenv("DISCORD_TOKEN")
GUILD: str = getenv('DISCORD_GUILD').split(',')
CHANNEL: str = getenv('DISCORD_CHANNEL').split(',')
ROLE_ADMIN: str = getenv('RAGNABOT_ROLE_ADMIN').split(',')
CMD_PREFIX: str = getenv("RAGNABOT_CMD_PREFIX")
DB_STRING: str = getenv("RAGNABOT_DB")
RAGNASONG_URL: str = "https://ragnasong.com/api/"
RAGNASONG_MAPS: str = RAGNASONG_URL + "/searchMap/?start={}&dificulty="
API_USER: str = getenv("API_USER")
API_PASS: str = getenv("API_PASS")
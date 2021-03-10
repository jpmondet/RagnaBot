#/usr/bin/env python3

from redis import StrictRedis
import json
from bson.json_util import dumps, loads
from pymongo import MongoClient, ASCENDING


# https://hackersandslackers.com/redis-py-python/
# https://github.com/mertaydogan/python-redis-mongodb/blob/master/mongo-redis.py

rcon = StrictRedis(host="127.0.0.1", port=6379, db=0, charset="utf-8",decode_responses=True)

RAGNABOT_DB = "mongodb://localhost:27017/"
client = MongoClient(RAGNABOT_DB)

db = client.ragnabot

col = db.csongs
print(col.name)
#csongs = list(db.csongs.find())
csongs_cached = loads(rcon.get('csongs'))

for i in range(1000):
    print(csongs_cached[-1])

#rcon.rpush('csongs', dumps(csongs))
#print(f"my_list: {rcon.lrange('csongs', 0, -1)}")
#print(csongs)

#rcon.echo("test")

#rcon.set('csongs', dumps(csongs))

#csongs_cached = loads(rcon.get('csongs'))
#for csong in csongs_cached:
#    print(csong['uuid'])
#print(loads(rcon.get('accounts')))



#print(db.accounts.find_one({ 'discord_id': '184936440797331457'}))
#print(db.accounts.find_one({ 'player_name': 'cptclawww'}))
#print(list(db.accounts.find({ 'player_name': re.compile('c', re.IGNORECASE)})))
#print(db.accounts.find_one({ 'player_name': re.compile('^' + 'cpt' + '$', re.IGNORECASE)}))
#db.accounts.delete_many({})
#db.accounts.insert_one({'player_name': 'name'})
#db.accounts.delete_one({'player_name': 'name'})
#print(db.accounts.count_documents({}))

#db.pending.delete_one({'map_uuid': '38510d20d9e75f781fe9676737c106098a909306', 'player_id': 3, 'difficulty_played': '1', 'score': '1234', 'misses': '3', 'perfects_percent': '86', 'triggers': '7', 'proof': 'https://me.com/img.png'})

#db.csongs.delete_many({})
#db.cslboards.delete_many({})
#db.players.delete_many({})
#db.maps_played.delete_many({})
#db.pending.delete_many({})
#db.accounts.delete_many({})
#
#print("\n\n\n\nCSONGS")
#print(list(db.csongs.find()))
#print("\n\n\n\CSLBOARDS")
#print(list(db.cslboards.find()))
#print("\n\n\n\PLAYERS")
#print(list(db.players.find()))
#print("\n\n\n\MAPS_PLAYED")
#print(list(db.maps_played.find()))
#print("\n\n\n\PENDING")
#print(list(db.pending.find()))
#print("\n\n\n\ACCOUNTS")
#print(list(db.accounts.find()))

#/usr/bin/env python3


from pymongo import MongoClient, ASCENDING
import re

# https://pymongo.readthedocs.io/en/stable/tutorial.html

RAGNABOT_DB = "mongodb://localhost:27017/"

client = MongoClient(RAGNABOT_DB)

db = client.ragnabot

print("\n\n\n\nCSONGS")
print(list(db.csongs.find()))
print("\n\n\n\CSLBOARDS")
print(list(db.cslboards.find()))
print("\n\n\n\PENDING")
print(list(db.pending.find()))
print("\n\n\n\ACCOUNTS")
print(list(db.accounts.find()))
print("\n\n\n\INDEX")
print(list(db.index_seq.find()))

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

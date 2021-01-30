#/usr/bin/env python3


from pymongo import MongoClient, ASCENDING

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
#db.accounts.delete_many({})
#db.accounts.insert_one({'player_name': 'name'})
#db.accounts.delete_one({'player_name': 'name'})
#print(db.accounts.count_documents({}))

db.csongs.delete_many({})
db.cslboards.delete_many({})
db.pending.delete_many({})
db.accounts.delete_many({})
db.index_seq.delete_many({})

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

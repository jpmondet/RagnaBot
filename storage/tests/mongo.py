#/usr/bin/env python3


from pymongo import MongoClient, ASCENDING

from utils.bot_utils import *

# https://pymongo.readthedocs.io/en/stable/tutorial.html

client = MongoClient(RAGNABOT_DB)

db = client.test

fruits = db.fruits

print(fruits.find_one({'origin': 'malaysia'}))

fruit_to_add  = {'name': 'kiwi' } 

fruit_id = fruits.insert_one(fruit_to_add).inserted_id

print(fruit_id)

print(fruits.find_one({'name': 'kiwi'}))

fruitzz = fruits.insert_many([{'name': 'banana'}, {'name': 'raspberry'}])

print(fruitzz)
for fruit in fruits.find({'name': 'kiwi'}):
#for fruit in fruits.find():
    print(fruit)

print(fruits.count_documents({}))

d = datetime.datetime(2020, 11, 12, 12)
print(d)

for fruit in fruits.find().sort("price"):
    print(fruit)


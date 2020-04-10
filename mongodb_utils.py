import os
import pymongo


mongodb_host = os.getenv('MONGODB_HOST')
mongodb_port = int(os.getenv('MONGODB_PORT'))
mongodb_db = os.getenv('MONGODB_DB')
mongodb_result_collection = os.getenv('MONGODB_RESULT_COLLECTION')
mongodb_user = os.getenv('MONGODB_USER')
mongodb_password = os.getenv('MONGODB_PASSWORD')
mongodb_auth_db = os.getenv('MONGODB_AUTH_DB')


print('connect mongodb')
# MONGODB config
client = pymongo.MongoClient(
    mongodb_host,
    mongodb_port,
    username=mongodb_user,
    password=mongodb_password,
    authSource=mongodb_auth_db
)
db = client[mongodb_db]
result_collection = db[mongodb_result_collection]
# create index, if exists - it won't create an error, just ignores
result_collection.create_index([("source", pymongo.ASCENDING),
                                ("object_type", pymongo.ASCENDING),
                                ("object_id", pymongo.ASCENDING)],
                               unique=True)


task = {}


def result_write_callback(posts):
    dublicate_count = None
    # insert result
    try:
        result_collection.insert_many(posts, ordered=False)
    except pymongo.errors.BulkWriteError as e:
        dublicate_count = len(e.details['writeErrors'])
        print(dublicate_count, '-')
        if not e.details['writeErrors'][0]['errmsg'].startswith('E11000 duplicate key error collection'):
            raise e

    return dublicate_count

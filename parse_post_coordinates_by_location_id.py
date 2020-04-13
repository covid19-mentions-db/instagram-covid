from mongodb_utils import result_collection, db
from instagram_utils import parse_location_batch
import os
from time import sleep, time
from pymongo import InsertOne, UpdateOne
from multiprocessing.dummy import Pool as ThreadPool


INSTAGRAM_LOCATION_COLLECTION = os.getenv('INSTAGRAM_LOCATION_COLLECTION', 'instagram_location')
BATCH_COUNT = int(os.getenv('BATCH_COUNT', '5000'))
WORKER_COUNT = int(os.getenv('WORKER_COUNT', '50'))


instagram_location_collection = db[INSTAGRAM_LOCATION_COLLECTION]


def worker(new_batch):
    result = parse_location_batch(new_batch)

    # prepare update commands
    batch_insert = []
    for res in result:
        _doc = {
            '_id': res[0]
        }
        _doc.update(res[1])

        insert_op = InsertOne(
            _doc
        )
        batch_insert.append(insert_op)

    # update
    try:
        instagram_location_collection.bulk_write(batch_insert, ordered=False)
    except Exception as e:
        print(e)
        raise e


def update_values_from_db(tasks, ids_in_db):
    # prepare update commands
    batch_update = []
    for task in tasks:
        location_id = task['location']['id']

        if location_id in ids_in_db:
            location = ids_in_db[location_id]
            if 'lat' in location:
                update_op = UpdateOne(
                    {
                        '_id': task['_id']
                    },
                    {
                        '$set': {'location.coordinates': [location['lat'], location['lon']]}
                    },
                    upsert=False,
                )
            elif 'location_status_code' in location:
                update_op = UpdateOne(
                    {
                        '_id': task['_id']
                    },
                    {
                        '$set': {'location_status_code': location['location_status_code']}
                    },
                    upsert=False,
                )
            else:
                raise RuntimeError('Something went wrong with location', location_id, location)

            batch_update.append(update_op)

    if batch_update:
        # update
        result_collection.bulk_write(batch_update, ordered=False)


def parse():
    task_count = 0

    while True:
        start_time = time()

        new_batch = result_collection.find(
            {
                'source': 'instagram',
                'object_type': 'post',
                'location.id': {'$exists': True},
                'location.coordinates': {'$exists': False},
                'location_status_code': {'$exists': False},
            },
            {
                '_id': 1,
                'location.id': 1
            }
        ).limit(BATCH_COUNT)

        if not new_batch:
            print('new batch is empty, sleep(6000)')
            sleep(6000)
            continue

        # extract values mongodb
        tasks = [elem for elem in new_batch]
        ids = []
        for task in tasks:
            location_id = task['location']['id']
            if location_id not in ids:
                ids.append(location_id)

        # check locations on db cache
        instagram_locations_in_db = instagram_location_collection.find({'_id': {'$in': ids}})
        ids_in_db = {}
        for elem in instagram_locations_in_db:
            ids_in_db[elem['_id']] = elem

        # update with already exist values
        update_values_from_db(tasks, ids_in_db)

        # other ids should be looked up in instagram
        new_tasks = list(ids - ids_in_db.keys())

        print(len(tasks), len(new_tasks), len(ids_in_db.keys()))
        if new_tasks:
            # split tasks per worker
            TASKS_PER_WORKER = int((len(new_tasks) / WORKER_COUNT))
            if TASKS_PER_WORKER < 2:
                TASKS_PER_WORKER = len(new_tasks)

            chunks = [new_tasks[x:x + TASKS_PER_WORKER] for x in range(0, len(new_tasks), TASKS_PER_WORKER)]

            # map tasks to workers
            pool_size = len(chunks)
            pool = ThreadPool(pool_size)
            res = pool.map(worker, chunks)
            pool.close()
            pool.join()

        task_count += 1
        print('task', task_count, 'finished', time() - start_time)


if __name__ == '__main__':
    print('start parsing post info bath')
    parse()

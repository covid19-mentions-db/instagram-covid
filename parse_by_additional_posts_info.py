from mongodb_utils import result_collection
from instagram_utils import parse_post_info_batch
import os
from time import sleep, time
from pymongo import UpdateOne
from multiprocessing.dummy import Pool as ThreadPool


BATCH_COUNT = int(os.getenv('BATCH_COUNT', '10000'))
WORKER_COUNT = int(os.getenv('WORKER_COUNT', '100'))
TASKS_PER_WORKER = int(BATCH_COUNT / WORKER_COUNT)


def worker(new_batch):
    result = parse_post_info_batch(new_batch)

    # prepare update commands
    batch_update = []
    for res in result:
        update_op = UpdateOne(
            {
                '_id': res[0]['_id']
            },
            {
                '$set': res[1]
            },
            upsert=False,
        )
        batch_update.append(update_op)

    # update
    result_collection.bulk_write(batch_update, ordered=False)


if __name__ == '__main__':
    print('start parsing post info batch')
    task_count = 0

    while True:
        start_time = time()

        new_batch = result_collection.find(
            {
                'source': 'instagram',
                'object_type': 'post',
                'author_name': {'$exists': False},
                'status_code': {'$exists': False},
            },
            {
                '_id': 1,
                'object_id': 1
            }
        ).limit(BATCH_COUNT)

        if not new_batch:
            print('new batch is empty, sleep(6000)')
            sleep(6000)
            continue

        # extract values mongodb
        tasks = [elem for elem in new_batch]
        # split tasks per worker
        chunks = [tasks[x:x + TASKS_PER_WORKER] for x in range(0, len(tasks), TASKS_PER_WORKER)]

        # map tasks to workers
        pool_size = WORKER_COUNT
        pool = ThreadPool(pool_size)
        res = pool.map(worker, chunks)
        pool.close()
        pool.join()

        task_count += 1
        print('task', task_count, 'finished', time() - start_time)

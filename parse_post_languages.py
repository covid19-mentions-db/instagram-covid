from mongodb_utils import result_collection
import os
from time import sleep, time
from langdetect import DetectorFactory, detect
from langdetect.detector import LangDetectException
from pymongo import UpdateOne


# https://pypi.org/project/langdetect/
# Language detection algorithm is non-deterministic, which means that if you try to run it on a text which is either
# too short or too ambiguous, you might get different results everytime you run it.
DetectorFactory.seed = 0
BATCH_COUNT = int(os.getenv('BATCH_COUNT', '10000'))
index_langs = ['da', 'nl', 'en', 'fi', 'fr', 'de', 'hu', 'it', 'nb', 'pt', 'ro', 'ru', 'es', 'sv', 'tr']


if __name__ == '__main__':
    print('start parsing post info bath')
    task_count = 0

    while True:
        start_time = time()

        new_batch = result_collection.find(
            {
                'source': 'instagram',
                'object_type': 'post',
                'lang': {'$exists': False},
            },
            {
                '_id': 1,
                'object_text': 1
            }
        ).limit(BATCH_COUNT)

        if not new_batch:
            print('new batch is empty, sleep(6000)')
            sleep(6000)
            continue

        batch_update = []
        i = 0
        for elem in new_batch:
            text = elem['object_text']

            if text:
                try:
                    lang = detect(text)
                except LangDetectException as e:
                    if str(e) == 'No features in text.':
                        lang = 'er'
                    else:
                        raise e
            else:
                lang = None

            _set = {'lang': lang}
            if lang in index_langs:
                _set['index_lang'] = lang

            update_op = UpdateOne(
                {
                    '_id': elem['_id']
                },
                {
                    '$set': _set
                },
                upsert=False,
            )
            batch_update.append(update_op)

            i += 1
            if i % 100 == 0:
                print(i)

        # update
        result_collection.bulk_write(batch_update, ordered=False)

        task_count += 1
        print('task', task_count, 'finished', time() - start_time)

from mongodb_utils import result_write_callback
from instagram_utils import parse_by_tag
import os
from time import sleep


_TAG = os.getenv('TAG', 'covid')


if __name__ == '__main__':
    print('start parsing for tag', _TAG)
    parse_by_tag(_TAG, write_callback=result_write_callback)

    print('task is completed' 'sleep(60000)')
    sleep(60000)

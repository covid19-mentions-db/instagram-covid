import requests
import random
import json
import os
import re


# if the post eralier than this time, it will be skipped
border_time = int(os.getenv('BORDER_TIME', '1575158400'))  # 1 Dec 2019


initial_headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 '
                  'Safari/537.36',
}

USE_PROXY = False
PROXIES_FILE_PATH_OR_URL = os.getenv('PROXIES_FILE_PATH_OR_URL')
PROXIES_TYPE = os.getenv('PROXIES_TYPE')
if PROXIES_FILE_PATH_OR_URL:
    m = re.search('^http(?:s|)://', PROXIES_FILE_PATH_OR_URL)
    if m:
        resp = requests.get(PROXIES_FILE_PATH_OR_URL)
        content = resp.text
    else:
        with open(PROXIES_FILE_PATH_OR_URL, 'r') as f:
            content = f.readlines()

    PROXIES = [x.strip() for x in content]
    USE_PROXY = True

READ_TIMEOUT = 30
TRY_COUNTS = 10


# get nes session with random proxy and guest token
def get_new_session():
    print('start getting new session')
    for _trying in range(TRY_COUNTS, -1, -1):
        try:
            # init session with default headers
            session = requests.session()
            session.headers.update(initial_headers)

            if USE_PROXY:
                # set proxy
                _proxy = random.choice(PROXIES)
                _proxy = {'https': '%s://%s' % (PROXIES_TYPE, _proxy)}
                session.proxies = _proxy

            print('getting new session successful')
            return session

        except Exception as e:
            print(e)
            if _trying == 0:
                raise Exception('try count exceeded')


POST_INFO_URL = 'https://www.instagram.com/p/%s/?__a=1'
LOCATION_INFO = 'https://www.instagram.com/explore/locations/%s/?__a=1'
GRAPHQL_API_URL = 'https://www.instagram.com/graphql/query/'
session = get_new_session()


def get_graphql_page(tag, count, end_cursor=None):
    global session
    variables = {
        'tag_name': tag.lower(),
        'first': int(count),
        'show_ranked': False
    }
    if end_cursor:
        variables['after'] = end_cursor
    query = {
        'query_hash': 'f92f56d47dc7a55b606908374b43a314',
        'variables': json.dumps(variables, separators=(',', ':'))
    }

    try_new_session = False
    for _trying in range(TRY_COUNTS, -1, -1):
        try:
            resp = session.get(GRAPHQL_API_URL, params=query)
            if resp.status_code == 200:
                return resp.json()

            print(resp.status_code, resp.text)
        except Exception as e:
            print(e)
            if _trying == 0:
                raise Exception('try count exceeded')

        # try new session from second try
        if try_new_session:
            session = get_new_session()
            try_new_session = False
        else:
            try_new_session = True

    raise Exception('try count exceeded')


def parse_edges(edges, tag):
    result = []
    if edges:
        for edge in edges:
            node = edge['node']

            if node['taken_at_timestamp'] < border_time:
                print('skip', node['shortcode'])
                continue

            # extract all the text
            edge_media_to_caption = node['edge_media_to_caption']
            edge_media_to_caption_edges = edge_media_to_caption['edges']
            text = '\n'.join([edge_media_to_caption_edge['node']['text']
                              for edge_media_to_caption_edge in edge_media_to_caption_edges])

            curr = {
                'source': 'instagram',
                'author_id': node['owner']['id'],
                # 'author_name': None,
                'object_type': 'post',
                'object_id': node['shortcode'],
                'object_text': text,
                'keyword': tag,
                # 'lang': tweet['lang'],
                # 'location': location,
                'time': node['taken_at_timestamp'],
                'likes_count': node['edge_liked_by']['count'],
                # 'reposts_count': None,
                'comments_count': node['edge_media_to_comment']['count'],
                'images': [node['thumbnail_src']],
            }

            result.append(curr)

    return result


def parse_by_tag(tag, write_callback=None, new_border_time=None, max_iterations_with_no_new_posts=None):
    global border_time
    if new_border_time:
        border_time = new_border_time
    iterations_with_no_new_posts = 0
    end_cursor = None

    extracted_count = 0
    while True:
        j = get_graphql_page(tag, 50, end_cursor=end_cursor)

        try:
            hashtag = j['data']['hashtag']
            edge_hashtag_to_media = hashtag['edge_hashtag_to_media']

            # extract posts
            edges = edge_hashtag_to_media['edges']
            posts = parse_edges(edges, tag)
            if max_iterations_with_no_new_posts:
                if posts:
                    iterations_with_no_new_posts = 0
                else:
                    iterations_with_no_new_posts += 1
                    if iterations_with_no_new_posts >= max_iterations_with_no_new_posts:
                        print('iterations_with_no_new_posts >= max_iterations_with_no_new_posts',
                              iterations_with_no_new_posts, max_iterations_with_no_new_posts)
                        print('so, we stop parsing')
                        break
            if posts and write_callback:
                dublicate_count = write_callback(posts)

            # is there any post left
            page_info = edge_hashtag_to_media['page_info']
            has_next_page = page_info.get('has_next_page')
            end_cursor = page_info.get('end_cursor')

            extracted_count += len(posts)
            print(len(posts), extracted_count, has_next_page, end_cursor)

            if end_cursor and has_next_page:
                continue
            print(json.dumps(j))
        except Exception as e:
            print(j)
            print(e)

        break


def get_page(url, private_session):
    try_new_session = False
    for _trying in range(TRY_COUNTS, -1, -1):
        try:
            resp = private_session.get(url, timeout=READ_TIMEOUT)
            if resp.status_code == 200:
                return resp.json(), private_session
            if resp.status_code == 404:
                return {'status_code': 404}, private_session

            print(resp.status_code, resp.text)
        except Exception as e:
            print(e)
            if _trying == 0:
                return {'status_code': 498}, private_session

        # try new session from second try
        if try_new_session:
            private_session = get_new_session()
            try_new_session = False
        else:
            try_new_session = True

    raise Exception(resp.status_code, resp.text, 'try count exceeded')


def parse_post_info_batch(batch):
    return_result = []
    private_session = get_new_session()

    for elem in batch:
        try:
            # get information from instagram
            object_id = elem['object_id']
            url = POST_INFO_URL % object_id
            result, private_session = get_page(url, private_session)

            if result.get('status_code') in [404, 498]:
                return_result.append([elem, result])
                print(object_id, result.get('status_code'))
                continue

            # parse
            shortcode_media = result['graphql']['shortcode_media']

            # owner
            res = {
                'author_name': shortcode_media['owner']['full_name'],
                'author_username': shortcode_media['owner']['username'],
            }

            # location
            location_dict = shortcode_media.get('location')
            if location_dict:

                location = {
                    'id': location_dict['id'],
                    'name': location_dict['name'],
                }

                try:
                    address_json = location_dict['address_json']
                    if address_json:
                        address_json = json.loads(address_json)
                        location['zip_code'] = address_json['zip_code']
                        location['city_name'] = address_json['city_name']
                        location['region_name'] = address_json['region_name']
                        location['country_code'] = address_json['country_code']
                except Exception as e:
                    print(1)

                res['location'] = location
            else:
                res['location'] = None

            return_result.append([elem, res])
            print(object_id, 'good')
        except Exception as e:
            print(elem, e)
            raise e

    return return_result


def parse_location_batch(batch):
    return_result = []
    private_session = get_new_session()

    for location_id in batch:
        try:
            # get information from instagram
            url = LOCATION_INFO % location_id
            result, private_session = get_page(url, private_session)

            if result.get('status_code') in [404, 498]:
                return_result.append([location_id, {'location_status_code': result.get('status_code')}])
                print(location_id, result.get('status_code'))
                continue

            location = result['graphql']['location']

            if not location['lat']:
                return_result.append([location_id, {'location_status_code': 406}])
                print(location_id, 406)
                continue

            res = {
                'lat': location['lat'],
                'lon': location['lng'],
            }

            return_result.append([location_id, res])
            print(location_id, 'good')
        except Exception as e:
            print(location_id, e)
            raise e

    return return_result


if __name__ == '__main__':
    # get_page('covid', 50)
    # parse_by_tag('covid')
    parse_post_info_batch([{'object_id': 'B-pQNLDhJFd'}])

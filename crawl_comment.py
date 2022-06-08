import requests
import random
import time
import concurrent.futures
import csv
import json

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
          'content-type': 'text'}


def retry_with_backoff(retries=5, backoff_in_seconds=1):
    def rwb(func):
        def wrapper(url):
            x = 0
            while True:
                try:
                    return func(url)
                except:
                    if x == retries:
                        raise
                    else:
                        sleep = (backoff_in_seconds * 2 ** x +
                                 random.uniform(0, 1))
                        time.sleep(sleep)
                        x += 1
        return wrapper
    return rwb


@retry_with_backoff()
def curl(url: str, timeout: int=10) -> dict:
    return requests.get(
        url,
        headers=HEADER,
        timeout=timeout
    ).json()


def get_all_data(url: str) -> list:
    data = curl(url)['data']
    return data['ratings']


def get_summary_rating(url: str) -> dict:
    return curl(url)['data']['item_rating_summary']


def get_neccesary_data(ratings: list) -> list:
    results = []
    try:
        for rating in ratings:
            results.append(
                {
                    'comment': rating['comment'],
                    'rating_star': rating['rating_star'],
                    'tags': rating['tags']
                }
            )
    except Exception as e:
        # logger.error(e)
        pass
    return results


def crawl_comment(item_id, shop_id, offset: int = 20, max_workers: int = 32):
    url = 'https://shopee.vn/api/v2/item/get_ratings?filter=0&flag=1&itemid={}&limit=50&offset=0&shopid={}&type=0'.format(item_id, shop_id)
    summary_rating = get_summary_rating(url)
    total_count = summary_rating['rcount_with_context']
    logger.info(f"There are {total_count} comments")
    futures = []
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for offset in range(0, total_count, offset):
            url = "https://shopee.vn/api/v2/item/get_ratings?filter=0&flag=1&itemid={}&limit=20&offset={}&shopid={}&type=0".format(item_id, offset, shop_id)
            futures.append(executor.submit(get_all_data, url))

    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())

    all_data = get_neccesary_data(results)
    length = len(all_data)
    logger.info(f"Successfully crawl all {length} comments")
    comments = {'summary_rating': summary_rating,
                'rating': all_data}
    return comments


with open('data.json', encoding='utf-8') as json_file:
    data = json.load(json_file)

all_comments = []

x = 0
for i in data:
    item_id = i['product_id']
    shop_id = i['shop_id']
    comments = crawl_comment(item_id, shop_id)
    all_comments.append(comments)
    x += 1
    if (x % 100) == 0:
        print('done:', x)

with open('comments.json', 'w', encoding='utf-8') as f:
    json.dump(all_comments, f, ensure_ascii=False, indent=4)


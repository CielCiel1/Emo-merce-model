import requests
import random
import time
import concurrent.futures
import csv
import json

HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
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
def curl(url: str, timeout: int = 10) -> dict:
    return requests.get(
        url,
        headers=HEADER,
        timeout=timeout
    ).json()


def get_all_data(url: str) -> dict:
    data = curl(url)
    results = data['data']
    return results


shop_id_list = []
with open('data.json', encoding='utf-8') as json_file:
    data = json.load(json_file)

for item in data:
    shop_id_list.append(item['shop_id'])
shop_id_list = list(set(shop_id_list))

shop_data = []
for id in shop_id_list:
    url = 'https://shopee.vn/api/v4/product/get_shop_info?shopid={}'.format(id)
    shop = get_all_data(url)
    necessary_data = {
        'shop_id': shop['shopid'],
        'name': shop['name'],
        'vacation': shop['vacation'],
        'location': shop['shop_location'],
        'is_official_shop': shop['is_official_shop'],
        'item_count': shop['item_count'],
        'rating_star': shop['rating_star'],
        'response_rate': shop['response_rate'],
        'update_at': shop['ctime'],
        'response_time': shop['response_time'],
        'follower': shop['follower_count'],
        'rating_bad': shop['rating_bad'],
        'rating_good': shop['rating_good'],
        'rating_normal': shop['rating_normal']
    }
    shop_data.append(necessary_data)

with open('shop_data.json', 'w', encoding='utf-8') as f:
    json.dump(shop_data, f, ensure_ascii=False, indent=4)


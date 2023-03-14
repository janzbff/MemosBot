#!/usr/bin/env python
# coding=utf-8

import asyncio
# import datetime

from urllib.parse import urlparse
from aiohttp.formdata import FormData
from aiohttp import ClientResponse, ClientTimeout
from aiohttp_retry import RetryClient, ClientSession
# from loguru import logger


class Request:
    def __init__(self, *args, **kwargs):
        self.client_session = ClientSession()
        self.retry_client = RetryClient(client_session=self.client_session)
        self.request = self.retry_client.request(*args, **kwargs)

    async def __aenter__(self) -> ClientResponse:
        return await self.request

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client_session.close()
        await self.retry_client.close()


def request(method, url, params=None, headers=None, data=None, json=None):
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    if json is not None:
        return Request(method, url, params=params, headers=headers, ssl=False, json=json,
                       timeout=ClientTimeout(total=1000))
    else:
        return Request(method, url, params=params, headers=headers, data=data, ssl=False,
                       timeout=ClientTimeout(total=1000))


def parse_text(text: str):
    text_list = text.split(' ')
    tags = []
    res_ids = []
    visibility = "PRIVATE"
    word_list = []
    for t in text_list:
        if t == '#PUBLIC':
            visibility = "PUBLIC"
        elif t.startswith('#'):
            tags.append(t.strip('#'))
            word_list.append(t)
        elif t.startswith('[') and t.endswith(']'):
            res_ids = [int(x) for x in list(eval(t))]
        else:
            word_list.append(t)
    texts = ' '.join(word_list)
    return texts, tags, visibility, res_ids


class Memo:
    def __init__(self, token):
        api = urlparse(token)
        self.netloc = api.netloc
        self.open_api = api.query
        self.scheme = api.scheme

    async def send_memo(self, text=None, visibility="PRIVATE", res_id_list=None):
        if res_id_list is None:
            res_id_list = []
        data = {
            "content": text,
            "visibility": visibility,
            "resourceIdList": res_id_list
        }
        path = 'api/memo'
        url = f'{self.scheme}://{self.netloc}/{path}?{self.open_api}'
        async with request("POST", url=url, json=data) as resp:
            assert resp.status == 200
            resp_data = await resp.json()
            return  resp_data['data']['id']

    async def archive_memo(self, memo_id):
        data = {'id': int(memo_id), 'rowStatus': 'ARCHIVED'}
        path = f'api/memo/{memo_id}'
        url = f'{self.scheme}://{self.netloc}/{path}?{self.open_api}'
        async with request("PATCH", url, json=data) as resp:
            assert resp.status == 200
            return

    async def update_memo(self, memo_id, text=None, visibility="PRIVATE", res_id_list=None):
        """
        目前只支持更新文字的memo，不支持更新资源
        :param memo_id:
        :param text:
        :param visibility:
        :param res_id_list:
        :return:
        """
        data = {
                    "id": memo_id,
                    "content": text,
                    "visibility": visibility,
                    "resourceIdList": res_id_list
                }
        path = f'api/memo/{memo_id}'
        url = f'{self.scheme}://{self.netloc}/{path}?{self.open_api}'
        async with request("PATCH", url, json=data) as resp:
            assert resp.status == 200
            return



class Resource:
    def __init__(self, token):
        api = urlparse(token)
        self.netloc = api.netloc
        self.open_api = api.query
        self.scheme = api.scheme

    async def create_res(self, res, filename):
        path = 'api/resource/blob'
        url = f'{self.scheme}://{self.netloc}/{path}?{self.open_api}'
        # filename = f'pic-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        data = FormData()
        data.add_field('file', res, filename=filename, content_type='image/jpeg')
        async with request("POST", url, data=data) as resp:
            assert resp.status == 200
            res_data = await resp.json()
            return res_data['data']['id']

class Tag:
    def __init__(self, token):
        api = urlparse(token)
        self.netloc = api.netloc
        self.open_api = api.query
        self.scheme = api.scheme

    async def create_tag(self, name):
        path = 'api/tag'
        url = f'{self.scheme}://{self.netloc}/{path}?{self.open_api}'
        data = {'name': name}
        async with request("POST", url, json=data) as resp:
            assert resp.status == 200


if __name__ == '__main__':
    memos = '#memos #public 测试文字解析 [1,2,3]'
    memo = Tag('http://localhost:3001/api/memo?openId=00118412EFA02227B49BD145D6F75940')
    asyncio.run(memo.create_tag('测试1'))
    # print(t,tags,v,res)







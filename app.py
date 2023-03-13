#!/usr/bin/env python
# coding=utf-8

import shelve
import asyncio

from urllib.parse import urlparse
from aiohttp import web
from telebot.async_telebot import AsyncTeleBot, types
from telebot.asyncio_filters import IsReplyFilter, TextStartsFilter
from dotenv import dotenv_values
from api import Memo, Resource, Tag


config = dotenv_values(".env")
bot = AsyncTeleBot(config['API_TOKEN'])

media_group_ids = {}

@bot.message_handler(commands=['start', 'help'])
async def send_auth(message):
    await bot.reply_to(message, '''
        不保存任何信息，但需要绑定Memos Open API用于推送。
        实现了文字、单张图文和多张图文的功能，日志功能有时间再说了。
        ''')


@bot.message_handler(commands=['bind'])
async def bind(message):
    markup = types.ForceReply(selective=False)
    await bot.send_message(message.chat.id, "请输入Memos Open Api.", reply_markup=markup)


@bot.message_handler(commands=['unbind'])
async def bind(message):
    with shelve.open('info.db', flag='c', protocol=None, writeback=True) as f:
        if str(message.chat.id) in f.keys():
            del f[str(message.chat.id)]
            await bot.reply_to(message, f'{message.chat.id}已经解绑，建议您去Memos后台重置api！')
        else:
            await bot.reply_to(message, f'{message.chat.id}未找到您的绑定信息！')


@bot.message_handler(is_reply=True, text_startswith='http')
async def save_info(message):
    if message.text.startswith("http"):
        with shelve.open('info.db', flag='c', protocol=None, writeback=False) as f:
            f[str(message.chat.id)] = message.text
        await bot.reply_to(message, f'{message.chat.id}绑定{message.text}成功！')
    if config['ADMIN_ID'] != '':
        try:
            await bot.send_message(config['ADMIN_ID'], f'{message.chat.id}注册')
        except ValueError as e:
            print(e)
    else:
        await bot.reply_to(message, "请输入正确的Memos Open API")


@bot.message_handler(is_reply=False, content_types=['text'])
async def send_memo_by_words(message):
    with shelve.open('info.db', flag='c', protocol=None, writeback=False) as f:
        if str(message.chat.id) in f.keys():
            url = f[str(message.chat.id)]
            o = urlparse(str(url))
            domain = f'{o.scheme}://{o.netloc}/m/'

        else:
            await bot.reply_to(message, "未绑定Memos Open API，请先绑定后再使用。")
            return
    try:
        memo = Memo(url)

        text, tags, visibility, res_ids = memo.parse_text(message.text)
        memo_id = await memo.send_memo(text=text, visibility=visibility, res_id_list=res_ids)
        memo_url = f'{domain}{memo_id}'

        memo_tag = Tag(url)
        for tag in tags:
            await memo_tag.create_tag(tag)
        await bot.reply_to(message, memo_url)
    except Exception as e:
        await bot.reply_to(message, f"出错了，重来吧！{e}")


media_ids = {}
@bot.message_handler(is_reply=False, content_types=['photo'])
async def send_memo_by_words_and_resource(message):
    with shelve.open('info.db', flag='c', protocol=None, writeback=False) as f:
        if str(message.chat.id) in f.keys():
            url = f[str(message.chat.id)]
        else:
            await bot.reply_to(message, "未绑定Memos Open API，请先绑定后再使用。")
            return
    file_path = await bot.get_file(message.photo[-1].file_id)
    downloaded_file = await bot.download_file(file_path.file_path)

    try:
        res = Resource(url)
        filename = file_path.file_path.split('/')[1]
        res_id = await res.create_res(downloaded_file, filename=filename)
        if message.media_group_id is not None:
            media_ids.setdefault(message.media_group_id, []).append(res_id)
        else:
            media_ids.setdefault(message.message_id, []).append(res_id)
        # markup = types.ForceReply(selective=False)
        await bot.reply_to(message, f'资源ID：{res_id}')
    except Exception as e:
        print("出错了")
        await bot.reply_to(message, f"出错了，重来吧！{e}")


@bot.message_handler(is_reply=True, content_types=['text', 'photo'])
async def send_memo_by_words(message):
    with shelve.open('info.db', flag='c', protocol=None, writeback=False) as f:
        if str(message.chat.id) in f.keys():
            url = f[str(message.chat.id)]
            o = urlparse(str(url))
            domain = f'{o.scheme}://{o.netloc}/m/'

        else:
            await bot.reply_to(message, "未绑定Memos Open API，请先绑定后再使用。")
            return

    try:
        memo = Memo(url)
        text, tags, visibility, _ = memo.parse_text(message.text)
        if message.reply_to_message.media_group_id:
            res_ids = media_ids[message.reply_to_message.media_group_id]
        else:
            res_ids = media_ids[message.reply_to_message.message_id]
        memo_id = await memo.send_memo(text=text, visibility=visibility, res_id_list=res_ids)
        memo_url = f'{domain}{memo_id}'
        memo_tag = Tag(url)
        for tag in tags:
            await memo_tag.create_tag(tag)
        await bot.reply_to(message, memo_url)
    except Exception as e:
        await bot.reply_to(message, f"出错了，重来吧！{e}")



bot.add_custom_filter(IsReplyFilter())
bot.add_custom_filter(TextStartsFilter())

#Process webhook calls
async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = types.Update.de_json(request_body_dict)
        asyncio.ensure_future(bot.process_new_updates([update]))
        return web.Response()
    else:
        return web.Response(status=403)


async def shutdown(app):
    await bot.remove_webhook()
    await bot.close_session()

async def setup():
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    await bot.remove_webhook()
    # Set webhook

    # await bot.set_webhook(url=config['WEBHOOK_URL_BASE'] + config['WEBHOOK_URL_PATH'])
    host = config['WEBHOOK_HOST']
    token = config['API_TOKEN']
    url = f'{host}/{token}/'
    await bot.set_webhook(url=url)

    app = web.Application()
    app.router.add_post('/{token}/', handle)
    app.on_cleanup.append(shutdown)
    return app


if __name__ == '__main__':
    if config['MODE'] == 'webhook':
        # Start aiohttp server
        web.run_app(
            setup(),
            host=config['WEBHOOK_LISTEN'],
            port=config['WEBHOOK_PORT']
        )
    elif config['MODE'] == 'polling':
        asyncio.run(bot.remove_webhook())
        print('polling')
        asyncio.run(bot.polling())
    else:
        pass
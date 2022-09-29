import os
import re
import asyncio
import _thread
import functions
import unicodedata
from time import sleep
from telebot import types
from unidecode import unidecode
from telethon.sync import TelegramClient
from datetime import datetime, timezone, timedelta
from functions import bold, t_me, italic, time_now, html_link
from telethon.tl.functions.channels import GetFullChannelRequest
# =================================================================================================================
stamp1 = time_now()
logging = []
log_enabled = False
functions.environmental_files(python=True)
list_commands = [types.BotCommand('last_message_id', '0')]
gold, castles = {'for': '-', 'lost': '+'}, '(🥔|🐺|🦅|🐉|🦌|🦈|🌑|🐢|☘)'
Auth = functions.AuthCentre(ID_DEV=-1001312302092, TOKEN=os.environ['TOKEN'], DEV_TOKEN=os.environ.get('DEV_TOKEN'))
bot_commands = Auth.bot.get_my_commands()
battle_shorts = {
    'were wiped out by a horde': '⚔😎',
    'was a bloody massacre, but the forces': '⚔⚡',
    'have easily fought off': '🛡👌',
    'had a slight edge over the armies': '🛡⚡',
    'were bored - no one': '🛡😴',
    'have stood victorious over the forces': '🛡',
    'successfully managed to break into the castle': '⚔'}

if bot_commands:
    last_message_id = int(bot_commands[0].description)
else:
    last_message_id = 25000
    Auth.bot.set_my_commands([types.BotCommand('last_message_id', str(last_message_id))])

if os.environ.get('local') is None:
    drive_client = functions.GoogleDrive('google.json')
    for file in drive_client.files():
        if file['name'] == f"{os.environ['session']}.session":
            drive_client.download_file(file['id'], file['name'])
# =================================================================================================================


async def sender(chat_id: int, text=None):
    await Auth.async_message(Auth.async_bot.send_message, id=chat_id, text=text)


def former(response: dict, lang: str = 'ru'):
    tz = timezone(timedelta(hours=0 if lang == 'en' else 3))
    title = 'Battle reports' if lang == 'en' else 'Сводки с полей'
    date = datetime.fromtimestamp(response['timestamp'], tz).strftime('%d/%m/%Y %H:%M')
    return f"{bold(f'⛳{title}:')}\n" \
           f"{response['text']}{html_link(response['link'], 'Battle' if lang == 'en' else 'Битва')} {italic(date)}"


def start(stamp):
    from timer import timer
    channel = os.environ['original']
    tz, channel = timezone(timedelta(hours=0)), int(channel) if channel.startswith('-100') else channel
    client = TelegramClient(os.environ['session'], int(os.environ['api_id']), os.environ['api_hash']).start()
    print(channel, type(channel), client.get_entity(channel))
    with client:
        if os.environ.get('local'):
            Auth.dev.printer(f'Запуск бота локально за {time_now() - stamp} сек.')
        else:
            Auth.dev.start(stamp)
            Auth.dev.printer(f'Бот запущен за {time_now() - stamp} сек.')
            _thread.start_new_thread(auto_reboot, ())
            _thread.start_new_thread(logger, ())

        while True:
            now = datetime.now(tz)
            delay = 10 if now.strftime('%H') in ['07', '15', '23'] else 100
            delay = 1 if int(now.strftime('%M')) < 30 else delay
            print('delay', delay)
            client.loop.run_until_complete(channel_handler(client, timer, channel))
            sleep(delay)


def auto_reboot():
    reboot = None
    tz = timezone(timedelta(hours=3))
    while True:
        try:
            sleep(30)
            date = datetime.now(tz)
            if date.strftime('%H') == '23' and date.strftime('%M') == '57':
                reboot = True
                while date.strftime('%M') == '57':
                    sleep(1)
                    date = datetime.now(tz)
            if reboot:
                reboot = None
                text, _ = Auth.logs.reboot()
                Auth.dev.printer(text)
        except IndexError and Exception:
            Auth.dev.thread_except()


async def channel_handler(client: TelegramClient, timer, channel):
    global last_message_id
    try:
        messages = await client.get_messages(channel, ids=[last_message_id + 1], limit=1)
        for message in messages:
            if message:
                last_message_id = message.id
                Auth.bot.set_my_commands([types.BotCommand('last_message_id', str(last_message_id))])
                response = await handler(client, timer, message)
                if response:
                    coroutines = []
                    for lang in ['ru', 'en']:
                        coroutines.append(sender(int(os.environ[f'{lang}_channel']), former(response, lang=lang)))
                    await asyncio.gather(*coroutines)
            else:
                Auth.dev.printer(f"Нет сообщения {t_me}{re.sub('-100', '', str(channel))}/{last_message_id + 1}")
    except IndexError and Exception:
        await Auth.dev.executive(None)


def logger():
    global logging, log_enabled
    print('logger() запущен')
    while True:
        tz = timezone(timedelta(hours=0))
        if datetime.now(tz).strftime('%H:%M') in ['07:00', '15:00', '23:00']:
            log_enabled = True
            sleep(600)
            log_enabled = False
        if logging:
            with open('report.txt', 'w') as report_file:
                for record in logging:
                    record_text = ''
                    for character in str(record):
                        replaced = unidecode(str(character))
                        if replaced != '':
                            record_text += replaced
                        else:
                            try:
                                record_text += f'[{unicodedata.name(character)}]'
                            except ValueError:
                                record_text += '[???]'
                    report_file.write(f'{record_text}\n')
            with open('report.txt', 'rb') as report_file:
                Auth.message(document=report_file, caption=f"Битва {datetime.now(tz).strftime('%H:%M')}")
            logging = []
        sleep(10)


async def handler(client: TelegramClient, timer, event):
    groups, scores, response = {'🛡': [], '⚔': []}, {}, {}
    trophies_search = re.search('Scores:(.*)', event.message, flags=re.DOTALL)
    date_search = re.search(r'(\d{2}) (.*) 10(\d{2})\nBattle reports:', event.message)
    if date_search and trophies_search:
        response.update({'text': '', 'timestamp': timer(date_search)})
        result = await client(GetFullChannelRequest(event.peer_id.channel_id))
        response['link'] = f'{t_me}{result.chats[0].username or event.peer_id.channel_id}/{event.id}'
        for row in event.message.split('\n\n'):
            castle_search = re.search(f'.*At {castles}.*?Castle', row)
            castle = castle_search.group(1) if castle_search else None
            if castle:
                response[castle] = '🔱' if '🔱' in row else ''
                stock_search = re.search(r'and (\d+) stock', row)
                gold_search = re.search(r'(for|lost) (\d+) gold', row)
                for short_text in battle_shorts:
                    if short_text in row:
                        response[castle] += battle_shorts.get(short_text)
                        break
                for key in groups:
                    groups[key].append(castle) if key in response[castle] else None
                if gold_search:
                    response[castle] += f" {gold.get(gold_search.group(1), '')}{gold_search.group(2)}💰"
                if stock_search:
                    response[castle] += f' -{stock_search.group(1)}📦' if stock_search.group(1) != '0' else ''

        for row in trophies_search.group(1).split('\n'):
            castle_search = re.search(rf'{castles}.+ \+(\d+) 🏆 points', row)
            if castle_search:
                castle, trophy = castle_search.groups()
                scores[castle] = int(castle_search.group(2))
                response.update({castle: f"{response.get(castle, '')} +{trophy}🏆".lstrip()})

        for castle_list in groups.values():
            for castle in scores:
                if castle in castle_list:
                    response['text'] += f"{italic(f'{castle}: {response.get(castle)}')}\n"
    else:
        link = f"{t_me}{re.sub('-100', '', os.environ['original'])}/{event.peer_id.channel_id}"
        Auth.dev.printer(f'Пост {link} не относится к дайджесту, пропущен.')
    return response


if __name__ == '__main__' and os.environ.get('local'):
    start(stamp1)

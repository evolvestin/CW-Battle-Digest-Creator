import os
import re
import objects
import _thread
import requests
from time import sleep
from bs4 import BeautifulSoup
from objects import bold, code, italic, stamper, printer, html_link

stamp1 = objects.time_now()
title = objects.bold('⛳Сводки с полей:') + '\n'
main_address = 'https://t.me/ChatWarsDigest/'
mini_address = 'https://t.me/CWDigest/'
castles = '(🐢|☘|🌹|🍁|🦇|🖤|🍆)'
idChannel = -1001492730228
idMe = 396978030
e_trident = '🔱'
battle_emoji = {
    'со значительным преимуществом': '⚔😎',
    'разыгралась настоящая бойня, но все-таки силы атакующих были ': '⚔⚡',
    'легко отбились от': '🛡👌',
    'героически отразили ': '🛡⚡',
    'скучали, на них ': '🛡😴',
    'успешно отбились от': '🛡',
    'успешно атаковали защитников': '⚔'
}

start_search = objects.query('https://t.me/UsefullCWLinks/4?embed=1', r'CW3: (\d+) :CW3.mini: (\d+) :mini.d: (.*) :d')
Auth = objects.AuthCentre(os.environ['TOKEN'])
bot = Auth.start_main_bot('non-async')
executive = Auth.thread_exec
if start_search:
    main_post_id = int(start_search.group(1))
    mini_post_id = int(start_search.group(2))
    objects.environmental_files(python=True)
    last_date = start_search.group(3)
    Auth.start_message(stamp1)
else:
    main_post_id = 0
    last_date = '\nОшибка с нахождением номера поста. ' + objects.bold('Бот выключен')
    Auth.start_message(stamp1, last_date)
    _thread.exit()
# ====================================================================================


def sender(text, date, channel):
    global last_date, mini_post_id, main_post_id
    bot.send_message(idChannel, text, parse_mode='HTML', disable_web_page_preview=True)
    sleep(4)
    if channel == 'main':
        main_post_id += 1
    else:
        mini_post_id += 1
    last_date = date
    try:
        start_editing = \
            bold('CW3: ') + code(main_post_id) + bold(' :CW3\n') + \
            bold('mini: ') + code(mini_post_id) + bold(' :mini\n') + \
            bold('d: ') + code(last_date) + bold(' :d\n')
        bot.edit_message_text(start_editing, -1001471643258, 4, parse_mode='HTML')
    except IndexError and Exception as error:
        executive(str(error))


def checker():
    from timer import timer
    global main_post_id, mini_post_id, last_date
    while True:
        try:
            sleep(0.1)
            printer_text = main_address + str(main_post_id)
            soup = BeautifulSoup(requests.get(printer_text + '?embed=1').text, 'html.parser')
            is_post_not_exist = soup.find('div', class_='tgme_widget_message_error')
            if is_post_not_exist is None:
                is_post_id_exist = soup.find('div', class_='tgme_widget_message_link')
                raw = str(soup.find('div', class_='tgme_widget_message_text js-message_text')).replace('<br/>', '\n')
                if is_post_id_exist:
                    soup = BeautifulSoup(raw, 'html.parser').get_text()
                    time_search = re.search(r'(\d\d) (.*) 10(..)\nРезультаты сражений:', soup)
                    if time_search:
                        reports = {}
                        soup = re.sub('.*\nРезультаты сражений:\n|️', '', soup)
                        trophy_search = re.search('По итогам сражений замкам начислено:(.*)', soup, flags=re.DOTALL)
                        for row in soup.split('\n\n'):
                            row = re.sub('По итогам сражений замкам начислено:.+', '', row, flags=re.DOTALL)
                            search_castle = re.search(castles, row)
                            if search_castle:
                                money_search = re.search('(на|отобрали) (.*) золотых монет', row)
                                box_search = re.search('потеряно (.*) складских ячеек', row)
                                castle = search_castle.group(1)

                                reports[castle] = ': '
                                if e_trident in row:
                                    reports[castle] += e_trident

                                for battle in battle_emoji:
                                    if battle in row:
                                        reports[castle] += battle_emoji.get(battle)
                                        break

                                if money_search:
                                    if money_search.group(1) == 'на':
                                        reports[castle] += ' -'
                                    elif money_search.group(1) == 'отобрали':
                                        reports[castle] += ' +'
                                    reports[castle] += money_search.group(2) + '💰'

                                if box_search:
                                    if box_search.group(1) != '0':
                                        reports[castle] += ' -' + box_search.group(1) + '📦'

                        if trophy_search:
                            letter = title
                            trophy_list = trophy_search.group(1).split('\n')
                            date = objects.log_time(timer(time_search), form='b_channel')
                            for row in trophy_list:
                                search = re.search(castles + r'.+ \+(\d+) 🏆 очков', row)
                                if search:
                                    castle, trophy = search.groups()
                                    letter += italic(castle + str(reports.get(castle)) + ' +' + trophy + '🏆') + '\n'
                            if stamper(date, '%d/%m/%Y %H:%M') > stamper(last_date, '%d/%m/%Y %H:%M'):
                                letter += html_link(printer_text, 'Битва') + ' ' + italic(date)
                                sender(letter, date, 'main')
                            else:
                                printer('пост ' + printer_text + ' уже был, пропускаю')
                                main_post_id += 1
                    else:
                        printer('пост ' + printer_text + ' не относится к дайджесту, пропускаю')
                        main_post_id += 1
            else:
                printer_text = mini_address + str(mini_post_id)
                soup = BeautifulSoup(requests.get(printer_text + '?embed=1').text, 'html.parser')
                is_post_not_exist = soup.find('div', class_='tgme_widget_message_error')
                if is_post_not_exist is None:
                    is_post_id_exist = soup.find('div', class_='tgme_widget_message_link')
                    raw = soup.find('div', class_='tgme_widget_message_text js-message_text')
                    raw = re.sub('️', '', re.sub('<br/>', '\n', str(raw)))
                    if is_post_id_exist:
                        is_post_battle = None
                        soup = BeautifulSoup(raw, 'html.parser').get_text()
                        for row in soup.split('\n'):
                            is_post_battle = re.search(r'Battle (\d{2}) (.*?) 10(\d{2})', row)
                            if is_post_battle:
                                break
                        if is_post_battle:
                            points = None
                            digest = None
                            date = objects.log_time(timer(is_post_battle), form='b_channel')
                            for part in soup.split('\n\n'):
                                points_search = re.search('🏆Очки:\n(.*)', part, flags=re.DOTALL)
                                digest_search = re.search('⛳Сводки с полей:\n(.*)', part, flags=re.DOTALL)
                                if digest_search:
                                    digest = digest_search.group(1).split('\n')
                                elif points_search:
                                    points = points_search.group(1).split('\n')
                            if stamper(date, '%d/%m/%Y %H:%M') > stamper(last_date, '%d/%m/%Y %H:%M'):
                                list_tags_a = BeautifulSoup(raw, 'html.parser').find_all('a')
                                battle_links = []
                                for tag_a in list_tags_a:
                                    if tag_a.get_text() == 'Battle':
                                        battle_links.append(tag_a.get('href'))
                                if len(battle_links) == 1:
                                    search_post = re.search(main_address, battle_links[0])
                                    if search_post:
                                        raw_post = re.sub(r'\D', '', re.sub(main_address, '', battle_links[0]))
                                        main_post_id = int(raw_post) + 1
                                        if points and digest:
                                            print(points)
                                            letter = title
                                            for row in digest:
                                                castle_row = re.search('(.*?): .*', row)
                                                points_text = ''
                                                if castle_row:
                                                    for point in points:
                                                        conform = re.search(castle_row.group(1) +
                                                                            r'.*: \+(\d+)', point)
                                                        if conform:
                                                            points_text += ' +' + conform.group(1) + '🏆'
                                                letter += italic(row + points_text) + '\n'
                                            letter += html_link(battle_links[0], 'Битва') + ' ' + italic(date)
                                            sender(letter, date, 'mini')
                            else:
                                printer('пост ' + printer_text + ' уже был, пропускаю')
                                mini_post_id += 1
                        else:
                            printer('пост ' + printer_text + ' не относится к дайджесту, пропускаю')
                            mini_post_id += 1
                else:
                    sleep(0.02)
        except IndexError and Exception:
            executive()


def telegram_polling():
    try:
        bot.polling(none_stop=True, timeout=60)
    except IndexError and Exception:
        bot.stop_polling()
        sleep(1)
        telegram_polling()


if __name__ == '__main__':
    _thread.start_new_thread(checker, ())
    telegram_polling()

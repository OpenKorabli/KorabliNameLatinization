import ctypes
import json
import os
import re
import string
import sys
import winreg
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import polib
import cyrtranslit
import xml.etree.ElementTree as Et

game_types: Dict[str, Tuple[str, bool]] = {
    'WOWS.RU.PRODUCTION': ('Lesta正式客户端', True),
    'WOWS.RPT.PRODUCTION': ('Lesta测试客户端', True),
    'MK.WW.PRODUCTION': ('Lesta正式客户端', True),
    'MK.PT.PRODUCTION': ('Lesta测试客户端', True),
    'WOWS.WW.PRODUCTION': ('Wargaming正式客户端', False),
    'WOWS.PT.PRODUCTION': ('Wargaming测试客户端', False)
}

msg_please_input = '请输入：'

msg_welcome: str =\
'''
欢迎使用Mir Korabley战舰名拉丁化工具~
注意：本工具仅适用于Mir Korabley(战舰世界莱服)，不适用于战舰世界[国服]或[直营服]
作者：
提出假想——walksQAQ
代码实现——北斗余晖
协议：GNU-LGPL-3.0(only)
仓库：https://github.com/OpenKorabli/KorabliNameLatinization
按回车键继续。
'''

msg_translit: str =\
'''
请选择是否需要进行西里尔字母拉丁化。
这将影响俄语战舰名的显示，以不惧为例：
不进行拉丁化显示——Неустрашимый
进行拉丁化后显示——Neustrashimy

进行拉丁化请输入字母Y，不进行拉丁化请输入字母N。
'''

default_dict: Dict[str, str] = {
  "Vermont (ЭМ)": "Vermont Test",
  "Корпус (по умолчанию)": "Hull (default)",
  "Goliath (ЭМ)": "Goliath Test",
  "M. Richthofen (ЭМ)": "M. Richthofen Test",
  "Manfred von Richthofen (ЭМ)": "Manfred von Richthofen Test",
  "Elbing (ЭМ)": "Elbing Test",
  "Manfred Richthofen (ЭМ)": "Manfred Richthofen Test",
  "Gouden Leeuw (ЭМ)": "Gouden Leeuw Test",
  "C. Colombo (ЭМ)": "C. Colombo Test",
  "Cristoforo Colombo (ЭМ)": "Cristoforo Colombo Test",
  "Venezia (ЭМ)": "Venezia Test",
  "Mikasa / ОФ-снаряды среднего калибра": "Mikasa / HE secondary shells",
  "Sazanami / стандартный корпус": "Sazanami / Standard Hull",
  "Mikasa / ББ-снаряды среднего калибра": "Mikasa / AP Secondary Shells",
  "Sazanami / облегчённый корпус": "Sazanami / Lightened Hull",
  "Комсомолец": "Komsomolets",
  "Серов": "Serov",
  "Победа": "Pobeda",
  "Нахимов": "Nakhimov",
  "Адмирал Нахимов": "Admiral Nakhimov",
  "Ульяновск": "Ulyanovsk",
  "Чкалов": "Chkalov",
  "Чкалов Ч": "Chkalov B",
  "Нахимов (ЭМ)": "Nakhimov Test",
  "Адмирал Нахимов (ЭМ)": "Admiral Nakhimov Test",
  "Николай I": "Nikolai I",
  "Император Николай I": "Imperator Nikolai I",
  "Князь Суворов": "Knyaz Suvorov",
  "Гангут": "Gangut",
  "Пётр Великий": "Pyotr Velikiy",
  "Измаил": "Izmail",
  "Синоп": "Sinop",
  "Владивосток": "Vladivostok",
  "Сов. Союз": "Sov. Soyuz",
  "Советский Союз": "Sovetsky Soyuz",
  "Кремль": "Kremlin",
  "Ушаков": "Ushakov",
  "Адмирал Ушаков": "Admiral Ushakov",
  "Сенявин": "Senyavin",
  "Адмирал Сенявин": "Admiral Senyavin",
  "Истомин": "Istomin",
  "Адмирал Истомин": "Admiral Istomin",
  "Корнилов": "Kornilov",
  "Адмирал Корнилов": "Admiral Kornilov",
  "Лазарев": "Lazarev",
  "Адмирал Лазарев": "Admiral Lazarev",
  "Бородино '04": "Borodino '04",
  "Окт. революция": "Okt. Revolutsiya",
  "Октябрьская революция": "Oktyabrskaya Revolutsiya",
  "Полтава": "Poltava",
  "Наварин": "Navarin",
  "Слава": "Slava",
  "П. коммуна": "P. Commune",
  "Парижская коммуна": "Paris Commune",
  "Новороссийск": "Novorossiysk",
  "Ленин": "Lenin",
  "Пермь Великая": "Perm Velikaya",
  "Североморск": "Severomorsk",
  "Топ Сикрет": "Top Secret",
  "Бородино": "Borodino",
  "Сов. Россия": "Sov. Russia",
  "Советская Россия": "Soviet Russia",
  "Красное Знамя": "Krasnoye Znamya",
  "В. И. Ленин": "V. I. Lenin",
  "Фрунзе": "Frunze",
  "Грузия": "Sakartvelo",
  "AL Сов. Россия": "AL Sov. Rossiya",
  "AL Советская Россия": [
    "AL Sovetskaya Rossiya",
    "AL Sov. Rossiya"
  ],
  "Несокрушимый": "Invincible",
  "Аврора": "Aurora",
  "Диана": "Diana",
  "Мурманск": "Murmansk",
  "Диана L": "Diana L",
  "Диана Lima": "Diana Lima",
  "Орлан": "Orlan",
  "Новик": "Novik",
  "Богатырь": "Bogatyr",
  "Светлана": "Svietlana",
  "Киров (OLD)": "Kirov (OLD)",
  "Киров (< 10.06.2020)": "Kirov (< 10.06.2020)",
  "Будённый": "Budyonny",
  "Щорс": "Shchors",
  "Чапаев": "Chapayev",
  "Дм. Донской": "Dm. Donskoi",
  "Дмитрий Донской": "Dmitri Donskoi",
  "Москва": "Moskva",
  "Новосибирск": "Novosibirsk",
  "Таллин": "Tallinn",
  "Рига": "Riga",
  "А. Невский": "A. Nevsky",
  "Александр Невский": "Alexander Nevsky",
  "Котовский": "Kotovsky",
  "Петропавловск": "Petropavlovsk",
  "Олег": "Oleg",
  "Красный Крым": "Krasny Krym",
  "Молотов": "Molotov",
  "Кутузов": "Kutuzov",
  "Михаил Кутузов": "Mikhail Kutuzov",
  "Кронштадт": "Kronshtadt",
  "Сталинград": "Stalingrad",
  "Громобой": "Gromoboy",
  "Варяг": "Varyag",
  "Микоян": "Mikoyan",
  "Керчь": "Kerch",
  "Лазо": "Lazo",
  "Щербаков": "Scherbakov",
  "Сталинград 2": "STALINGRAD #2",
  "AL Аврора": "AL Avrora",
  "Киров": "Kirov",
  "Молотов Ч": "Molotov B",
  "Очаков": "Ochakov",
  "Тольятти": "Togliatti",
  "Смоленск Ч": "Smolensk B",
  "П. Багратион": "P. Bagration",
  "Пётр Багратион": "Pyotr Bagration",
  "Ю. Долгорукий": "Y. Dolgoruky",
  "Юрий Долгорукий": "Yuri Dolgoruky",
  "Багратион": "Bagration",
  "Рус. Аляска": "Rus. Alaska",
  "Русская Аляска": "Russian Alaska",
  "Д. Пожарский": "D. Pozharsky",
  "Дмитрий Пожарский": "Dmitry Pozharsky",
  "Свердловск": "Sverdlovsk",
  "Лазо Ч": "Lazo B",
  "Макаров": "Makarov",
  "Адмирал Макаров": "Admiral Makarov",
  "Смоленск": "Smolensk",
  "Севастополь": "Sevastopol",
  "Комиссар": "Komissar",
  "Железная Аврора": "Iron Aurora",
  "[Москва]": "[Moskva]",
  "Железный Новик": "Iron Novik",
  "Макаров У": "Makarov U",
  "Макаров (учебный)": "Makarov (Training)",
  "Железный Варяг": "Iron Varyag",
  "Иван Калита": "Ivan Kalita",
  "Князь Владимир": "Prince Vladimir",
  "Петропавловск (ЭМ)": "Petropavlovsk Test",
  "Гремящий": "Gremyashchy",
  "Сторожевой": "Storozhevoi",
  "Дерзкий": "Derzki",
  "Изяслав": "Izyaslav",
  "Гневный (OLD)": "Gnevny (OLD)",
  "Гневный (< 06.03.2017)": "Gnevny (< 06.03.2017)",
  "Огневой (OLD)": "Ognevoi (OLD)",
  "Огневой (< 06.03.2017)": "Ognevoi (< 06.03.2017)",
  "Удалой": "Udaloi",
  "Ташкент (OLD)": "Tashkent (OLD)",
  "Ташкент (< 06.03.2017)": "Tashkent (< 06.03.2017)",
  "Киев (OLD)": "Kiev (OLD)",
  "Киев (< 06.03.2017)": "Kiev (< 06.03.2017)",
  "Хабаровск": "Khabarovsk",
  "Зоркий": "Zorkiy",
  "Подвойский": "Podvoisky",
  "Гневный": "Gnevny",
  "Минск": "Minsk",
  "Огневой": "Ognevoi",
  "Осмотрительный": "Osmotritelny",
  "Грозовой": "Grozovoi",
  "Опытный": "Opytniy",
  "Сообразительный": "Soobrazitelny",
  "Киев": "Kiev",
  "Находка": "Nakhodka",
  "Смелый": "Smely",
  "Спокойный": "Spokoiny",
  "Горделивый": "Gordelivy",
  "Ташкент": "Tashkent",
  "Дельный": "Delny",
  "Бойкий": "Boykiy",
  "Охотник": "Okhotnik",
  "Ленинград": "Leningrad",
  "Современный": "Sovremenny",
  "Ташкент '39": "Tashkent '39",
  "Неустрашимый": "Neustrashimy",
  "[Грозовой]": "[Grozovoi]",
  "Упорный": "Uporny",
  "С-1": "S-1",
  "Л-20": "L-20",
  "К-1": "K-1",
  "Б-4": "B-4",
  "С-189": "S-189",
  "С-189 Ч": "S-189 B",
  "К-41": "K-41",
  "Орлан (A)": "Orlan (A)",
  "Орлан (B)": "Orlan (B)",
  "Бородино / ББ-снаряды среднего калибра": "Borodino / AP Secondary Shells",
  "Громобой / ББ-снаряды среднего калибра": "Gromoboy / AP Secondary Shells",
  "Бойкий / стандартный корпус": "Boykiy / Standard Hull",
  "Бойкий / утяжелённый корпус": "Boykiy / Reinforced Hull",
  "Громобой / ОФ-снаряды среднего калибра": "Gromoboy / HE Secondary Shells",
  "Бородино / ОФ-снаряды среднего калибра": "Borodino / HE Secondary Shells",
  "Сторожевой (A)": "Storozhevoi (A)",
  "Сторожевой (B)": "Storozhevoi (B)",
  "Новик (А)": "Novik (A)",
  "Новик (B)": "Novik (B)",
  "К. Суворов (А)": "K. Suvorov (A)",
  "К. Суворов (В)": "K. Suvorov (B)",
  "Дерзкий (A)": "Derzki (A)",
  "Дерзкий (B)": "Derzki (B)",
  "Богатырь (А)": "Bogatyr (A)",
  "Богатырь (B)": "Bogatyr (B)",
  "Изяслав (A)": "Izyaslav (A)",
  "Изяслав (B)": "Izyaslav (B)",
  "Гангут (А)": "Gangut (A)",
  "Гангут (В)": "Gangut (B)",
  "Комсомолец (A)": "Komsomolets (A)",
  "Комсомолец (B)": "Komsomolets (B)",
  "Светлана (A)": "Svietlana (A)",
  "Светлана (B)": "Svietlana (B)",
  "Пётр Великий (А)": "Pyotr Velikiy (A)",
  "Пётр Великий (В)": "Pyotr Velikiy (B)",
  "Котовский (A)": "Kotovsky (A)",
  "Котовский (B)": "Kotovsky (B)",
  "Гневный (A)": "Gnevny (A)",
  "Гневный (B)": "Gnevny (B)",
  "Подвойский (A)": "Podvoisky (A)",
  "Подвойский (B)": "Podvoisky (B)",
  "Киров (A)": "Kirov (A)",
  "Киров (B)": "Kirov (B)",
  "Огневой (A)": "Ognevoi (A)",
  "Огневой (B)": "Ognevoi (B)",
  "Измаил (A)": "Izmail (A)",
  "Измаил (B)": "Izmail (B)",
  "Серов (A)": "Serov (A)",
  "Серов (B)": "Serov (B)",
  "Будённый (A)": "Budyonny (A)",
  "Будённый (B)": "Budyonny (B)",
  "С-1 (A)": "S-1 (A)",
  "С-1 (B)": "S-1 (B)",
  "Молотов Ч.": "Molotov B",
  "Лазо Ч.": "Lazo B.",
  "Удалой (A)": "Udaloi (A)",
  "Удалой (B)": "Udaloi (B)",
  "Минск (A)": "Minsk (A)",
  "Минск (B)": "Minsk (B)",
  "Синоп (A)": "Sinop (A)",
  "Синоп (B)": "Sinop (B)",
  "Ташкент '39": "Tashkent '39",
  "Щорс (A)": "Shchors (A)",
  "Щорс (B)": "Shchors (B)",
  "Чкалов Ч.": "Chkalov B.",
  "Ташкент (A)": "Tashkent (A)",
  "Ташкент (B)": "Tashkent (B)",
  "Киев (A)": "Kiev (A)",
  "Киев (B)": "Kiev (B)",
  "Владивосток (A)": "Vladivostok (A)",
  "Владивосток (B)": "Vladivostok (B)",
  "Л-20 (A)": "L-20 (A)",
  "Таллин (A)": "Tallinn (A)",
  "Таллин (B)": "Tallinn (B)",
  "В. И. Ленин": "V. I. Lenin",
  "Чапаев (A)": "Chapayev (A)",
  "Чапаев (B)": "Chapayev (B)",
  "Победа (A)": "Pobeda (A)",
  "Победа (B)": "Pobeda (B)",
  "Л-20 (B)": "L-20 (B)",
  "С-189 Ч.": "S-189 B",
  "Осмотрительный (A)": "Osmotritelny (A)",
  "Осмотрительный (B)": "Osmotritelny (B)",
  "Ашхабад (A)": "Ashkhabad (A)",
  "Ашхабад (B)": "Ashkhabad (B)",
  "С. Союз (А)": "S. Soyuz (A)",
  "С. Союз (В)": "S. Soyuz (B)",
  "Дмитрий Донской (A)": "Dmitri Donskoi (A)",
  "Дмитрий Донской (B)": "Dmitri Donskoi (B)",
  "Дмитрий Донской (C)": "Dmitri Donskoi (C)",
  "Рига (B)": "Riga (B)",
  "Рига (A)": "Riga (A)",
  "Находка (A)": "Nakhodka (A)",
  "Р-10": "R-10",
  "Смоленск Ч.": "Smolensk B.",
  "Halland (ЭМ)": "Halland Test",
  "Авианосец": "Aircraft Carrier",
  "Пучеглаз": "Lobster-Eyed",
  "Мститель": "Avenger",
  "Геракл": "Heracles ",
  "Крякадако": "Quackaducko",
  "У.Т.К.А.": "D.U.C.K.",
  "Святозар": "Svyatozar",
  "Шипоспин": "Thornridge",
  "Валькирия": "Valkyrie",
  "Штормовой": "Gale",
  "Шустрый": "Swift",
  "Неожиданный": "Unexpected",
  "Изворотливый": "Agile",
  "Л. МакКрякки": "L. McQuacci",
  "Луиджи МакКрякки": "Luigi McQuacci",
  "Фьюро": "Furo",
  "Корабль": "Ship",
  "Ядрёный": "Atomic Rage",
  "Шальной": "Seascythe",
  "Клыкорук": "Fangblade",
  "Молниеносный": "Whirlwind",
  "Гектор": "Hector",
  "Дон де ла Дак": "Don de la DuQue",
  "Дак Панчис": "Duck Punchis",
  "Кроха": "Zipper Sub",
  "Минный заградитель": "Minelayer",
  "Царь-корпус": "Tsar Hull",
  "Корпус «Таранный»": "\"Ramming\" Hull",
  "Корпус «Повышенная боеспособность»": "\"Increased HP\" Hull",
  "Корпус «Скоростной»": "\"Swift\" Hull",
  "Корпус «Универсальный»": "Multi-Purpose Hull",
  "Корпус «Повышенная манёвренность»": "\"Increased Maneuverability\" Hull",
  "Корпус «Бронированный»": "\"Armored\" Hull",
  "Корпус «Противоторпедный»": "\"Anti-Torpedo\" Hull",
  "Корпус «Аккумулирующий»": "\"Accumulating\" Hull",
  "Корпус «Повышенный лимит зарядов»": "\"Increased Charge Limit\" Hull",
  "Корпус «Ускоренное распределение зарядов»": "\"Accelerated Redistribution of Charges\" Hull",
  "Обтекаемое покрытие": "Sleek Skin",
  "Защитный панцирь": "Armor Shell",
  "Хитиновая броня": "Chitin Armor",
  "Кольчуга": "Chain Armor"
}

current_dict: Dict[str, str] = {}

def latinization(ru: polib.MOFile, _should_latinize_russian_ships: bool) -> Optional[polib.MOFile]:
    try:
        processed = polib.MOFile()
        processed.metadata = ru.metadata
        ships_list = [ent.msgid for ent in ru if not ent.msgid_plural and is_ship_relevant(ent.msgid)]
        for ent in ru:
            if ent.msgid not in ships_list:
                continue
            if _should_latinize_russian_ships and not ent.msgid.endswith('DESCR') and re.search(r'[\u0400-\u04FF]', ent.msgstr):
                ent.msgstr = translit(ent.msgstr)
            ent.msgstr = process_space(ent.msgstr)
            processed.append(ent)
        return processed
    except Exception as ex:
        print('处理文件时出现错误：')
        print(ex)
        return None


def translit(original: str):
    for space_var in [original, original.replace(' ', ' '), original.replace(' ', ' ')]:
        if space_var in current_dict:
            return current_dict[space_var]
    return cyrtranslit.to_latin(original, 'ru')

def process_space(msg: str) -> str:
    return msg.replace(' ', ' ')

def is_ship_relevant(msgid: str) -> bool:
    if 'H2020' in msgid and 'DESC' in msgid:
        return False
    ship_name_pattern = r'^IDS_P[A-Z]+S[A-Z]+(\d{3}(?:_(?:FULL|DESCR))?|\d{4}(?:_(?:FULL|DESCR))?)$'
    ship_hull_name_pattern = r'^IDS_P[A-Z]+UH\d{3}.*$'
    return bool(re.match(ship_name_pattern, msgid)) or bool(re.match(ship_hull_name_pattern, msgid))


def find_games(_pref_paths: List[Path]) -> Dict[Path, Tuple[str, bool]]:
    _games_all: Dict[Path, Tuple[str, bool]] = {}
    for _pref_path in _pref_paths:
        try:
            pref_root = Et.parse(_pref_path).getroot()
            games_block = pref_root.find('.//application/games_manager/games')
            _games = games_block.findall('.//game')
            if not _games:
                continue
            _paths = [Path(game.find('working_dir').text) for game in _games if game.find('working_dir') is not None]
            path_info_all = {_path : get_game_info(_path) for _path in _paths}
            for _p in path_info_all:
                _games_all[_p] = path_info_all[_p]
        except Exception:
            pass
    return _games_all


def get_game_info(_path: Path) -> (str, bool):
    game_info_file = _path.joinpath('game_info.xml')
    if not game_info_file.is_file():
        # For Steam Clients
        if _path.joinpath('steam_api64.dll').is_file():
            if _path.joinpath('Korabli.exe').is_file():
                return 'Lesta Steam客户端', True
            elif _path.joinpath('WorldOfWarships.exe').is_file():
                return 'WG Steam客户端', False
            else:
                return '未知Steam客户端', False
        else:
            return '未知路径', False
    try:
        game_info = Et.parse(game_info_file)
        game_id = game_info.find('.//game/id')
        if game_id is None:
            return 'Lesta未知客户端', False
        return match_game_info(game_id.text)
    except Exception:
        return 'Lesta未知客户端', False


def match_game_info(_game_id: str) -> (str, bool):
    if _game_id in game_types:
        return game_types[_game_id]
    else:
        return f'未知({_game_id})', False

def check_path_availability(_path_str: str) -> List[Path]:
    _path = Path(_path_str)
    if not _path.exists():
        print(f'路径{_path}不存在！')
        return []
    _game_info = get_game_info(_path)
    if _game_info[1]:
        return [_path,]
    else:
        _choice = input(f'检测到{_path_str}路径所对应的游戏类型为{_game_info[0]}，可能为错误路径。是否坚持向该路径安装？若是，请输入字母Y后按回车键：')
        if _choice.strip().upper() == 'Y':
            return [_path,]
        else:
            return []



def find_lgc_pref_paths() -> List[Path]:
    _pref_paths: Dict[str, Path] = {}
    print('正通过注册表寻找Lesta Game Center路径…')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\lgc\DefaultIcon') as key:
        lgc_dir_str, _ = winreg.QueryValueEx(key, '')
        if lgc_dir_str is not None:
            if ',' in lgc_dir_str:
                lgc_dir_str = lgc_dir_str.split(',')[0]
            preferences_path = Path(lgc_dir_str).parent.joinpath('preferences.xml')
            try:
                if preferences_path.is_file():
                    _pref_paths[str(preferences_path.absolute())] = preferences_path
            except Exception:
                print('未能通过注册表找到Lesta Game Center。')
                pass
    for pref_path in find_pref_manually():
        _pref_paths[str(pref_path.absolute())] = pref_path
    return [path for path in _pref_paths.values()]

def find_pref_manually() -> List[Path]:
    print('正在遍历可能的Lesta Game Center路径。')
    possible_lgc_pref_paths: List[Path] = []
    for drive in find_all_drives():
        try:
            target = Path(drive).joinpath('ProgramData').joinpath('Lesta').joinpath('GameCenter').joinpath('preferences.xml')
            if target.is_file():
                possible_lgc_pref_paths.append(target)
        except Exception:
            continue
    print(f'通过遍历找到的路径：{possible_lgc_pref_paths}' if possible_lgc_pref_paths else '未能通过遍历找到Lesta Game Center。')
    return possible_lgc_pref_paths


def find_all_drives() -> List[str]:
    return ['%s:/' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]


def do_latinization_for_game(_game_path: Path, _should_latinize_russian_ships: bool) -> bool:
    print(f'正在为{str(_game_path.absolute())}下的游戏执行战舰名拉丁化…')
    bin_path = _game_path.joinpath('bin')
    print('正在检索潜在的版本文件夹…')
    numeric_paths = []

    # 遍历目录下的所有子文件夹
    for name in os.listdir(bin_path):
        _path = bin_path.joinpath(name)
        if os.path.isdir(_path) and name.isdigit():
            numeric_paths.append(_path)

    if numeric_paths:
        print("已找到以下潜在的版本文件夹：")
        for _path in numeric_paths:
            print(_path)

        at_least_1_success = False

        for _path in numeric_paths:
            if do_latinization_for_build(_path, _should_latinize_russian_ships):
                at_least_1_success = True

        return at_least_1_success
    else:
        print("未找到任何潜在的版本文件夹：")
        return False


def do_latinization_for_build(_build_path: Path, _should_latinize_russian_ships: bool) -> bool:
    print(f'正在为{str(_build_path.absolute())}下的版本执行战舰名拉丁化…')
    ru_mo_path = _build_path.joinpath('res').joinpath('texts').joinpath('ru').joinpath('LC_MESSAGES').joinpath('global.mo')
    ru_mo: Optional[polib.MOFile] = None
    if not ru_mo_path.is_file():
        print('未找到俄文语言文件。已跳过该版本。')
        return False
    else:
        try:
            ru_mo = polib.mofile(str(ru_mo_path.absolute()))
        except Exception:
            print('俄文语言文件解析失败。已跳过该版本。')
    latinized = latinization(ru_mo, _should_latinize_russian_ships)
    if latinized is None:
        print('已跳过该版本。')
        return False
    try:
        target_path = _build_path.joinpath('res_mods').joinpath('texts').joinpath('ru').joinpath('LC_MESSAGES').joinpath('zzz_ok_latinization.mo')
        os.makedirs(target_path.parent, exist_ok=True)
        latinized.save(str(target_path.absolute()))
        return True
    except Exception as ex:
        print('保存失败，出现异常：')
        print(ex)
        return False


def main():
    input(msg_welcome)
    os.makedirs('dict', exist_ok=True)
    dict_file = Path('dict').joinpath('dict.json')
    print('正在检查字典文件…')
    if not dict_file.is_file():
        print(f'正在将默认字典写入到{str(dict_file.absolute())}')
        with open(dict_file, 'w', encoding='utf-8') as f:
            json.dump(default_dict, f, indent=2, ensure_ascii=False)
    if not current_dict:
        with open(dict_file, 'r', encoding='utf-8') as f:
            temp_dict = json.load(f)
        for key in temp_dict:
            if isinstance(temp_dict[key], str):
                current_dict[key] = temp_dict[key]
    pref_paths: List[Path] = []
    print('正在识别Lesta Game Center路径…')
    try:
        pref_paths = find_lgc_pref_paths()
    except Exception as ex:
        print('识别Lesta Game Center路径时发生错误：')
        print(ex)
    available_paths: List[Path] = []
    selections: Dict[int, (Path, str, bool)] = {}
    if pref_paths:
        print('找到如下游戏路径：')
        games = find_games(pref_paths)
        i = 0
        for game in games:
            i += 1
            selections[i] = game, games[game][0], games[game][1]
            print(f'{i}.[{games[game][0]}]:{str(game.absolute())}')
        available_paths = [game_path for game_path in games if games[game_path][1]]
    trigger_1st = True
    while not available_paths:
        if trigger_1st:
            trigger_1st = False
            print('未能找到符合条件(WG客户端)的路径。')
        print('请在以上游戏路径中选择其一输入其序号，或手动输入完整路径，或将路径文件夹拖拽到本程序的控制台窗口中；再按回车键。')
        new_path = input(msg_please_input)
        new_path = check_path_availability(new_path)
        if new_path:
            available_paths = new_path
    succeed_paths: List[Path] = []
    should_latinize_russian_ships = None
    while should_latinize_russian_ships is None:
        print(msg_translit)
        choice = str(input(msg_please_input)).strip().upper()
        if choice == 'Y':
            should_latinize_russian_ships = True
            print('进行拉丁化。')
        elif choice == 'N':
            should_latinize_russian_ships = False
            print('不进行拉丁化。')
        else:
            print('请正确输入字母Y或字母N。')
    for available_path in available_paths:
        try:
            if do_latinization_for_game(available_path, should_latinize_russian_ships):
                succeed_paths.append(available_path)
        except Exception as _ex:
            print(f'为{str(available_path.absolute())}路径下的游戏执行战舰名拉丁化时发生异常：')
            print(_ex)
    if succeed_paths:
        print('已为下列路径下的游戏执行战舰名拉丁化：')
        for succeed_path in succeed_paths:
            print(str(succeed_path.absolute()))

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run():
    try:
        main()
    except Exception as ex:
        print('主程序出现异常：')
        print(ex)
    input('按回车键退出。')

if __name__ == '__main__':
    dev_env = sys.executable.endswith('python.exe')
    if dev_env:
        run()
    else:
        os.chdir(Path(sys.executable).parent)
        if is_admin():
            run()
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)

# pipreqs . --ignore ".venv" --force
# pyinstaller -i resources/icon.ico --version-file=resources/version_file.txt latinization.py --clean
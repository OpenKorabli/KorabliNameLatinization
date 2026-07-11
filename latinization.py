import ctypes
import os
import re
import string
import sys
import winreg
import xml.etree.ElementTree as Et
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import mk_latinizer
import polib

game_types: Dict[str, Tuple[str, bool]] = {
    'MK.RU.PRODUCTION': ('Mir Korabley正式客户端', True),
    'MK.RPT.PRODUCTION': ('Mir Korabley测试客户端', True),
    'MK.PT.PRODUCTION': ('Mir Korabley测试客户端', True),
    'WOWS.WW.PRODUCTION': ('WoWs正式客户端', False),
    'WOWS.PT.PRODUCTION': ('WoWs测试客户端', False)
}

msg_please_input = '请输入：'

msg_welcome: str = \
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

msg_translit: str = \
    '''
    请选择是否需要进行西里尔字母拉丁化。
    这将影响俄语战舰名的显示，以不惧为例：
    不进行拉丁化显示——Неустрашимый
    进行拉丁化后显示——Neustrashimy
    
    进行拉丁化请输入字母Y，不进行拉丁化请输入字母N。
    '''


def latinization(ru: polib.MOFile, _should_latinize_russian_ships: bool) -> Optional[polib.MOFile]:
    try:
        processed = polib.MOFile()
        processed.metadata = ru.metadata
        ships_list = [ent.msgid for ent in ru if not ent.msgid_plural and is_ship_relevant(ent.msgid)]
        for ent in ru:
            if ent.msgid not in ships_list:
                continue
            if _should_latinize_russian_ships and not ent.msgid.endswith('DESCR') and re.search(r'[\u0400-\u04FF]',
                                                                                                ent.msgstr):
                ent.msgstr = mk_latinizer.to_latin(ent.msgstr)
            ent.msgstr = process_space(ent.msgstr)
            processed.append(ent)
        return processed
    except Exception as ex:
        print('处理文件时出现错误：')
        print(ex)
        return None


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
            path_info_all = {_path: get_game_info(_path) for _path in _paths}
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
        return [_path, ]
    else:
        _choice = input(
            f'检测到{_path_str}路径所对应的游戏类型为{_game_info[0]}，可能为错误路径。是否坚持向该路径安装？若是，请输入字母Y后按回车键：')
        if _choice.strip().upper() == 'Y':
            return [_path, ]
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
            target = Path(drive).joinpath('ProgramData').joinpath('Lesta').joinpath('GameCenter').joinpath(
                'preferences.xml')
            if target.is_file():
                possible_lgc_pref_paths.append(target)
        except Exception:
            continue
    print(
        f'通过遍历找到的路径：{[str(_path) for _path in possible_lgc_pref_paths]}' if possible_lgc_pref_paths else '未能通过遍历找到Lesta Game Center。')
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
    ru_mo_path = _build_path.joinpath('res').joinpath('texts').joinpath('ru').joinpath('LC_MESSAGES').joinpath(
        'global.mo')
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
        target_path = _build_path.joinpath('res_mods').joinpath('texts').joinpath('ru').joinpath(
            'LC_MESSAGES').joinpath('zzz_ok_latinization.mo')
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
            print('未能找到符合条件(Mir Korabley客户端)的路径。')
        print(
            '请在以上游戏路径中选择其一输入其序号，或手动输入完整路径，或将路径文件夹拖拽到本程序的控制台窗口中；再按回车键。')
        new_path = input(msg_please_input)
        if new_path.isnumeric():
            new_path = check_path_availability(selections.get(int(new_path))[0])
        else:
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

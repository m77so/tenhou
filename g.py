"""牌譜実況プログラム"""
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import math
from enum import Enum
from functools import cmp_to_key
# https://gist.github.com/nullpos/d6a10e1f4b1f906d8b6d

ARCHIVE_URL = 'http://e.mjv.jp/0/log/archived.cgi?'
PLAIN_URL = 'http://e.mjv.jp/0/log/plainfiles.cgi?'


def pstr(num):
    """牌を数字から文字列に変換する"""

#    hai = ["一", "二", "三", "四", "五", "六", "七", "八", "九",
#           "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨",
#           "1", "2", "3", "4", "5", "6", "7", "8", "9",
#           "東", "南", "西", "北", "白", "發", "中"]
#    return hai[num >> 2]
    num >>= 2
    
    if num >= 27:
        num -= 27
        if num == 4:
            num = 6
        elif num == 6:
            num = 4
    num += 7
    num = (num)+0x1f000

    return chr(num)


class Style(Enum):
    CASUAL = 1
    FORMAL = 2


class Player:
    """Player"""
    DAN = [
        "新人", "９級", "８級", "７級", "６級", "５級", "４級", "３級", "２級", "１級",
        "初段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段", "十段",
        "天鳳", "RESERVED..."]

    def __init__(self, name):
        self.name = urllib.parse.unquote(name)


def fulou(val):
    if val & 0x4:
        # 順
        t_10 = val >> 10
        t = math.floor(t_10 / 3)
        r = t_10 % 3
        if r == 0:
            return "\\" + pstr(t << 2) + pstr((t + 1) << 2) + pstr((t + 2) << 2)
        elif r == 1:
            return "\\" + pstr((t + 1) << 2) + pstr((t) << 2) + pstr((t + 2) << 2)
        elif r == 2:
            return "\\" + pstr((t + 2) << 2) + pstr((t) << 2) + pstr((t + 1) << 2)
    elif val & 0x8:
        # 刻子
        t = math.floor((val >> 9) / 3)
        kui = val & 0x3
        if kui == 1:
            return pstr(t << 2) + pstr(t << 2) + "\\" + pstr(t << 2)
        elif kui == 2:
            return pstr(t << 2) + "\\" + pstr(t << 2) + pstr(t << 2)
        elif kui == 3:
            return "\\" + pstr(t << 2) + pstr(t << 2) + pstr(t << 2)
    elif val & 0x10:
        # 加槓
        t = math.floor((val >> 9) / 3)
        kui = val & 0x3
        if kui == 1:
            return pstr(t << 2) + pstr(t << 2) + \
                "\\" + pstr(t << 2) + "\\" + pstr(t << 2)
        elif kui == 2:
            return pstr(t << 2) + "\\" + pstr(t << 2) \
                + "\\" + pstr(t << 2) + pstr(t << 2)
        elif kui == 3:
            return "\\" + pstr(t << 2) + "\\" + pstr(t << 2) \
                + pstr(t << 2) + pstr(t << 2)
    else:
        # 明槓・槓
        t = (val >> 10)
        kui = val & 0x3
        if kui == 1:
            return pstr(t << 2) + pstr(t << 2) + pstr(t << 2) + "\\" + pstr(t << 2)
        elif kui == 2:
            return pstr(t << 2) + "\\" + pstr(t << 2) + pstr(t << 2) + pstr(t << 2)
        elif kui == 3:
            return "\\" + pstr(t << 2) + pstr(t << 2) + pstr(t << 2) + pstr(t << 2)
        else:
            return pstr(t << 2) + pstr(t << 2) + pstr(t << 2) + pstr(t << 2)


class Game:
    def __init__(self):
        self.name = ""
        self.round = []
        self.is_sanma = None
        self.grade = None
        self.type = ""
        self.typecode = None
        self.Style = Style.FORMAL

    def go(self, type):
        self.typecode = type
        self.isSanma = True if type & 0x10 else False
        self.grade = ((type & 0x80) >> 7) + ((type & 0x20) >> 4)

        if self.isSanma:
            self.type += "三"

        self.type += "般上特鳳"[self.grade]
        if type & 8:
            self.type += "南"
        else:
            self.type += "東"
        if not(type & 4):
            self.type += "喰"
        if not(type & 2):
            self.type += "赤"
        if type & 0x40:
            self.type += "速"

    def un(self, attrib):
        self.player = []  # type: List[Player]
        self.player.append(Player(attrib["n0"]))
        self.player.append(Player(attrib["n1"]))
        self.player.append(Player(attrib["n2"]))
        if not(self.typecode & 0x10):
            self.player.append(Player(attrib["n3"]))

    def init(self, attrib):
        seed = list(map(int, attrib["seed"].split(",")))
        ten = attrib["ten"].split(",")
        if hasattr(self, "current_round"):
            self.round.append(self.current_round)
        self.current_round = Round(seed, ten, self)

    def agari(self, attrib):

        self.current_round.agari(attrib)

    def zimo(self, tag):
        self.current_round.zimo(ord(tag[0]) - 19 - 65, int(tag[1:]))

    def dapai(self, tag):
        self.current_round.zimo(ord(tag[0]) - 3 - 65, int(tag[1:]))


class Round:
    YAKU_FORMAL = [
        # 一飜
        "門前清自摸和", "立直", "一発", "槍槓", "嶺上開花",
        "海底摸月", "河底撈魚", "平和", "断幺九", "一盃口",
        "自風 東", "自風 南", "自風 西", "自風 北",
        "場風 東", "場風 南", "場風 西", "場風 北",
        "役牌 白", "役牌 發", "役牌 中",
        # 二飜
        "両立直", "七対子", "混全帯幺九", "一気通貫", "三色同順",
        "三色同刻", "三槓子", "対々和", "三暗刻", "小三元", "混老頭",
        # 三飜
        "二盃口", "純全帯幺九", "混一色",
        # 六飜
        "清一色",
        # 満貫
        "人和",
        # 役満
        "天和", "地和", "大三元", "四暗刻", "四暗刻単騎", "字一色",
        "緑一色", "清老頭", "九蓮宝燈", "純正九蓮宝燈", "国士無双",
        "国士無双１３面", "大四喜", "小四喜", "四槓子",
        # 懸賞役
        "ドラ", "裏ドラ", "赤ドラ"
    ]
    YAKU = [
        # 一飜
        "ツモ", "立直", "一発", "槍槓", "嶺上",
        "海底", "河底", "平和", "断幺九", "一盃口",
        "東", "南", "西", "北",
        "東", "南", "西", "北",
        "白", "發", "中",
        # 二飜
        "ダブリー", "チートイ", "チャンタ", "一通", "三色",
        "三色同刻", "三槓子", "トイトイ", "三暗刻", "小三元", "混老頭",
        # 三飜
        "二盃口", "純チャン", "混一",
        # 六飜
        "清一",
        # 満貫
        "人和",
        # 役満
        "天和", "地和", "大三元", "四暗刻", "四暗刻単騎", "字一色",
        "緑一色", "清老頭", "九蓮宝燈", "純正九蓮宝燈", "国士無双",
        "国士無双１３面", "大四喜", "小四喜", "四槓子",
        # 懸賞役
        "ドラ", "裏", "赤"
    ]
    KYOKU = [
        "東1局", "東2局", "東3局", "東4局",
        "南1局", "南2局", "南3局", "南4局",
        "西1局", "西2局", "西3局", "西4局",
        "北1局", "北2局", "北3局", "北4局",
    ]

    def __init__(self, seed, ten, game: Game):
        self.seed = seed
        self.game = game
        self.init_ten = ten
        print('\n\n{0}{1}本場'.format(self.KYOKU[seed[0]], seed[1]))

    def zimo(self, hito, pai):
        pass

    def dapai(self, hito, pai):
        pass

    def agari(self, attrib):
        hai = list(map(int, attrib["hai"].split(",")))
        machi = int(attrib["machi"])
        ten = list(map(int, attrib["ten"].split(",")))
        who = int(attrib["who"])
        fromwho = int(attrib["fromWho"])
        yaku = list(map(int, attrib["yaku"].split(",")))
        yaku = zip(*[iter(yaku)] * 2)
        sc = list(map(int, attrib["sc"].split(",")))
        sc = list(zip(*[iter(sc)] * 2))
        m = list(map(int, attrib["m"].split(","))) if "m" in attrib else []

        dora = list(map(int, attrib["doraHai"].split(",")))
        ba = list(map(int, attrib["ba"].split(",")))

        text = "ツモ " if who == fromwho else "ロン "
        text += self.game.player[who].name
        text += ("<-" + self.game.player[fromwho].name) \
            if who != fromwho else ""
        text += "\n"
        for h in hai:
            if machi != h:
                text += pstr(h)
        for f in m:
            text += " " + fulou(f)
        text += " " + pstr(machi)
        text += "  ドラ:"

        for h in dora:
            text += pstr(h)
        if hasattr(attrib, "doraHaiUra"):
            uradora = attrib["doraHaiUra"].split(",")
            text += " 裏ドラ:"
            for h in uradora:
                text += pstr(h)
        text += "\n"
        han = 0
        casual_yaku = []

        def cmp_casual(a, b):
            a = a[0]
            b = b[0]
            if a == 0:
                a = 6.5
            if b == 0:
                b = 6.5
            if a < b:
                return -1
            elif a == b:
                return 0
            else:
                return 1
        for y in yaku:
            han += y[1]
            if self.game.print == Style.FORMAL:
                text += self.YAKU_FORMAL[y[0]] + " " + str(y[1]) + "翻" + "\n"
            elif self.game.print == Style.CASUAL:
                casual_yaku.append(y)
        sorted(casual_yaku, key=cmp_to_key(cmp_casual))
        if self.game.print == Style.CASUAL:
            for y in casual_yaku:
                if y[0] >= 52:
                    if y[1] >= 1:
                        text += self.YAKU[y[0]] + str(y[1])
                else:
                    text += self.YAKU[y[0]]
        text += "\n" + str(ten[0]) + "符" + str(han) + "翻" + str(ten[1]) + "点"
        text += '\nリーチ棒{0}本,{1}本場\n'.format(ba[0], ba[1])
        for k, s in enumerate(sc):
            text += self.game.player[k].name + " " + str(s[0]) + "00 "
            if s[1] != 0:
                text += ("(+"if s[1] > 0 else "(") + str(s[1]) + "00)"
            text += "\n"
        print(text)
        return text


def download(urlid):
    req = urllib.request.Request(ARCHIVE_URL + urlid)
    try:
        with urllib.request.urlopen(req) as response:
            data = response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            try:
                req = urllib.request.Request(PLAIN_URL + urlid)
                with urllib.request.urlopen(req) as response:
                    data = response.read()
            except urllib.error.HTTPError as e:
                pass
    except urllib.error.URLError as e:
        pass

    XmlData = data.decode('utf-8')
    root = ET.fromstring(XmlData)
    game = Game()
    game.print = Style.CASUAL
    for child in root:
        if child.tag == "GO":
            game.go(int(child.attrib["type"]))
            print(game.type)
        elif (child.tag)[0:2] == "UN":
            game.un(child.attrib)
        elif (child.tag) == "TAIKYOKU":
            pass
        elif child.tag == "INIT":
            game.init(child.attrib)
        elif child.tag == "AGARI":
            game.agari(child.attrib)
        elif (child.tag) in {"GO", "DORA"}:
            print(child.tag, child.attrib)
        elif (child.tag)[0] in {"T", "U", "V", "W"}:
            game.zimo(child.tag)
        elif (child.tag)[0] in {"D", "E", "F", "G"}:
            game.dapai(child.tag)
        elif child.tag in {"SHUFFLE", "REACH", "N", "BYE"}:
            pass
        else:
            print(child.tag, child.attrib)

    return


if __name__ == '__main__':
    download("2017051200gm-0089-0000-a6392280")

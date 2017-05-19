"""牌譜実況プログラム"""
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import math
# https://gist.github.com/nullpos/d6a10e1f4b1f906d8b6d

ARCHIVE_URL = 'http://e.mjv.jp/0/log/archived.cgi?'
PLAIN_URL = 'http://e.mjv.jp/0/log/plainfiles.cgi?'


def pai(num):
    """牌を数字から文字列に変換する"""

    hai = ["一", "二", "三", "四", "五", "六", "七", "八", "九",
           "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨",
           "1", "2", "3", "4", "5", "6", "7", "8", "9",
           "東", "南", "西", "北", "白", "發", "中"]
    return hai[num >> 2]


def zimo(tag):
    """自摸"""

    hito = chr(ord(tag[0]) - 19) + "さん"
    str = pai(int(tag[1:]))
    print(hito + "の自摸" + str)


def dapai(tag):
    """打牌"""

    hito = chr(ord(tag[0]) - 3) + "さん"
    str = pai(int(tag[1:]))
    print(hito + "の打牌" + str)


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
            return pai(t << 2) + pai((t + 1) << 2) + pai((t + 2) << 2)
        elif r == 1:
            return pai((t + 1) << 2) + pai((t) << 2) + pai((t + 2) << 2)
        elif r == 2:
            return pai((t + 2) << 2) + pai((t) << 2) + pai((t + 1) << 2)
    elif val & 0x8:
        # 刻子
        t = math.floor((val >> 9) / 3)
        kui = val & 0x3
        if kui == 1:
            return pai(t << 2) + pai(t << 2) + "\\" + pai(t << 2)
        elif kui == 2:
            return pai(t << 2) + "\\" + pai(t << 2) + pai(t << 2)
        elif kui == 3:
            return "\\" + pai(t << 2) + pai(t << 2) + pai(t << 2)
    elif val & 0x10:
        # 加槓
        t = math.floor((val >> 9) / 3)
        kui = val & 0x3
        if kui == 1:
            return pai(t << 2) + pai(t << 2) + \
                "\\" + pai(t << 2) + "\\" + pai(t << 2)
        elif kui == 2:
            return pai(t << 2) + "\\" + pai(t << 2) \
                               + "\\" + pai(t << 2) + pai(t << 2)
        elif kui == 3:
            return "\\" + pai(t << 2) + "\\" + pai(t << 2) \
                + pai(t << 2) + pai(t << 2)
    else:
        # 明槓・槓
        t = (val >> 10)
        kui = val & 0x3
        if kui == 1:
            return pai(t << 2) + pai(t << 2) + pai(t << 2) + "\\" + pai(t << 2)
        elif kui == 2:
            return pai(t << 2) + "\\" + pai(t << 2) + pai(t << 2) + pai(t << 2)
        elif kui == 3:
            return "\\" + pai(t << 2) + pai(t << 2) + pai(t << 2) + pai(t << 2)
        else:
            return pai(t << 2) + pai(t << 2) + pai(t << 2) + pai(t << 2)


class Game:
    def __init__(self):
        self.name = ""
        self.round = []

    def go(self, type):
        self.type = ""
        self.typecode = type
        if type & 0x10:
            self.type += "三"
        if type & 0xA0 == 0xA0:
            self.type += "鳳"
        elif type & 0x20:
            self.type += "特"
        elif type & 0x80:
            self.type += "上"
        else:
            self.type += "般"
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
        "ツモ", "立直", "一発", "槍槓", "嶺上開花",
        "海底摸月", "河底撈魚", "平和", "断幺九", "一盃口",
        "東", "南", "西", "北",
        "東", "南", "西", "北",
        "白", "發", "中",
        # 二飜
        "ダブリー", "チートイ", "チャンタ", "一通", "三色",
        "三色同刻", "三槓子", "トイトイ", "三暗刻", "小三元", "混老頭",
        # 三飜
        "リャンペー", "純チャン", "混一",
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
        print('{0}{1}本場'.format(self.KYOKU[seed[0]], seed[1]))

    def agari(self, attrib):
        hai = list(map(int, attrib["hai"].split(",")))
        machi = int(attrib["machi"])
        ten = list(map(int, attrib["ten"].split(",")))
        who = int(attrib["who"])
        fromwho = int(attrib["fromWho"])
        yaku = list(map(int, attrib["yaku"].split(",")))
        yaku = zip(*[iter(yaku)] * 2)
        m = list(map(int, attrib["m"].split(","))
                 ) if hasattr(attrib, "m") else []
        dora = list(map(int, attrib["doraHai"].split(",")))
        ba = list(map(int, attrib["ba"].split(",")))

        text = "ツモ" if who == fromwho else "ロン"
        text += self.game.player[who].name
        text += ("放銃" + self.game.player[fromwho].name) \
            if who != fromwho else ""
        text += "\n"
        for h in hai:
            text += pai(h)
        for f in m:
            text += " " + fulou(f)
        text += " " + pai(machi)
        text += "\n ドラ:"

        for h in dora:
            text += pai(h)
        if hasattr(attrib, "doraHaiUra"):
            uradora = attrib["doraHaiUra"].split(",")
            text += " 裏ドラ:"
            for h in uradora:
                text += pai(h)
        text += "\n"
        han = 0
        for y in yaku:
            text += self.YAKU_FORMAL[y[0]] + " " + str(y[1]) + "翻" + "\n"
            han += y[1]
        text += str(ten[0]) + "符" + str(han) + "翻" + str(ten[1]) + "点"
        text += '\nリーチ棒{0}本,{1}本場'.format(ba[0], ba[1])
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
        print(e.value)

    XmlData = data.decode('utf-8')
    root = ET.fromstring(XmlData)
    game = Game()

    for child in root:
        print(child.tag, child.attrib)
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
            zimo(child.tag)
        elif (child.tag)[0] in {"D", "E", "F", "G"}:
            dapai(child.tag)
        else:
            print(child.tag, child.attrib)
    return


if __name__ == '__main__':
    download("2017051200gm-0089-0000-a6392280")

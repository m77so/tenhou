"""牌譜実況プログラム"""
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import math

from enum import Enum
from functools import cmp_to_key
# https://gist.github.com/nullpos/d6a10e1f4b1f906d8b6d
import io
import sys
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
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
    num = (num) + 0x1f000

    return chr(num)


class Style(Enum):
    CASUAL = 1
    FORMAL = 2


class Fulou:
    class FulouType(Enum):
        CHI = 1
        PONG = 2
        ANKAN = 3
        MINKAN = 4
        KAKAN = 5

    def __init__(self, val):
        self.pai = ""
        self.type = None

        if val & 0x4:
            # 順
            self.type = self.FulouType.CHI
            t_10 = val >> 10
            t = math.floor(t_10 / 3)
            r = t_10 % 3
            if r == 0:
                self.pai = "\\" + pstr(t << 2) + pstr((t + 1) <<
                                                      2) + pstr((t + 2) << 2)
            elif r == 1:
                self.pai = "\\" + pstr((t + 1) << 2) + \
                    pstr((t) << 2) + pstr((t + 2) << 2)
            elif r == 2:
                self.pai = "\\" + pstr((t + 2) << 2) + \
                    pstr((t) << 2) + pstr((t + 1) << 2)
        elif val & 0x8:
            # 刻子
            self.type = self.FulouType.PONG
            t = math.floor((val >> 9) / 3)
            kui = val & 0x3
            if kui == 1:
                self.pai = pstr(t << 2) + pstr(t << 2) + "\\" + pstr(t << 2)
            elif kui == 2:
                self.pai = pstr(t << 2) + "\\" + pstr(t << 2) + pstr(t << 2)
            elif kui == 3:
                self.pai = "\\" + pstr(t << 2) + pstr(t << 2) + pstr(t << 2)
        elif val & 0x10:
            # 加槓
            self.type = self.FulouType.KAKAN
            t = math.floor((val >> 9) / 3)
            kui = val & 0x3
            if kui == 1:
                self.pai = pstr(t << 2) + pstr(t << 2) + \
                    "\\" + pstr(t << 2) + "\\" + pstr(t << 2)
            elif kui == 2:
                self.pai = pstr(t << 2) + "\\" + pstr(t << 2) \
                    + "\\" + pstr(t << 2) + pstr(t << 2)
            elif kui == 3:
                self.pai = "\\" + pstr(t << 2) + "\\" + pstr(t << 2) \
                    + pstr(t << 2) + pstr(t << 2)
        else:
            # 明槓・槓
            self.type = self.FulouType.MINKAN
            t = (val >> 10)
            kui = val & 0x3
            if kui == 1:
                self.pai = pstr(t << 2) + pstr(t << 2) + \
                    pstr(t << 2) + "\\" + pstr(t << 2)
            elif kui == 2:
                self.pai = pstr(t << 2) + "\\" + pstr(t << 2) + \
                    pstr(t << 2) + pstr(t << 2)
            elif kui == 3:
                self.pai = "\\" + pstr(t << 2) + pstr(t << 2) + \
                    pstr(t << 2) + pstr(t << 2)
            else:
                self.type = self.FulouType.ANKAN
                self.pai = pstr(t << 2) + pstr(t << 2) + \
                    pstr(t << 2) + pstr(t << 2)

    def type_str(self):
        if self.type == self.FulouType.PONG:
            return "ポン"
        elif self.type == self.FulouType.CHI:
            return "チー"
        else:
            return "カン"


class Player:
    """Player"""
    DAN = [
        "新人", "９級", "８級", "７級", "６級", "５級", "４級", "３級", "２級", "１級",
        "初段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段", "十段",
        "天鳳", "RESERVED..."]

    def __init__(self, name):
        self.name = urllib.parse.unquote(name)


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

        if hasattr(self, "current_round"):
            self.round.append(self.current_round)
        self.current_round = Round()
        return self.current_round.init(attrib, self)

    def agari(self, attrib):

        return self.current_round.agari(attrib)

    def zimo(self, tag):
        return self.current_round.zimo(ord(tag[0]) - 19 - 65, int(tag[1:]))

    def dapai(self, tag):
        return self.current_round.dapai(ord(tag[0]) - 3 - 65, int(tag[1:]))

    def naki(self, attrib):
        return self.current_round.naki(int(attrib["who"]), int(attrib["m"]))

    def ryuukyoku(self, attrib):
        return self.current_round.ryuukyoku(attrib)
    
    def reach(self,attrib):
        return self.current_round.reach(attrib)



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

    class Mopai:
        def __init__(self, hito: int, mo: int):
            self.player = hito
            self.id = id
            self.junme = None
            self.nokori = None
            self.mo = None
            self.dapai = None

    def __init__(self):
        self.seed = None
        self.mopai = []
        self.player_mopai = []

    def init(self, attrib, game: Game):
        seed = list(map(int, attrib["seed"].split(",")))
        ten = list(map(int, attrib["ten"].split(",")))
        self.seed = seed
        self.game = game
        self.init_ten = ten

        for i in self.game.player:
            self.player_mopai.append([])
        hougaku = "東南西北"
        sekijun = ""
        for i, player in enumerate(self.game.player):
            sekijun += '{0}:{1}({2}00) '.format(
                hougaku[(-seed[0] + i) % 4], player.name, self.init_ten[i])
        return ('\n\n{0}{1}本場 {2}'.format(self.KYOKU[seed[0]], seed[1], sekijun))

    def zimo(self, hito, pai):
        mopai = self.Mopai(hito, pai)
        self.mopai.append(mopai)
        self.player_mopai[hito].append(mopai)
        mopai.junme = len(self.player_mopai[hito])
        mopai.id = len(self.mopai)

    def dapai(self, hito, pai):
        self.mopai[-1].dapai = pai

    def naki(self, who, m):
        self.zimo(who, m)
        f = Fulou(m)

        return '{3} {0} {1}順目 {2}'.format(
            self.game.player[who].name, len(self.player_mopai[who]), f.pai, f.type_str())

    def ba_tostr(self, b):
        b = list(map(int, b.split(",")))
        return 'リーチ棒{0}本,{1}本場'.format(b[1], b[0])

    def sc_tostr(self, sc, *, owari=False):
        text = ""
        sc = list(map(float, sc.split(",")))
        sc = list(zip(*[iter(sc)] * 2))
        for k, s in enumerate(sc):
            text += self.game.player[k].name + " " + str(int(s[0])) + "00 "
            if s[1] != 0 and not owari:
                text += ("(+"if s[1] > 0 else "(") + str(int(s[1])) + "00)"
            elif owari:
                text += ("(+"if s[1] > 0 else "(") + str(s[1]) + ")"
            text += "\n"
        return text
    
    def reach(self,attrib):
        step = int(attrib["step"])
        who = int(attrib["who"])
        if step == 1:
            return "立直 {0} {1}順目".format(self.game.player[who].name, len(self.player_mopai[who]))

    def ryuukyoku(self, attrib):
        text = "流局"
        for key in range(0, 3):
            if "hai" + str(key) in attrib:
                text += "\n"
                for h in list(map(int, attrib["hai" + str(key)].split(","))):
                    text += pstr(h)
        text += "\n" + self.sc_tostr(attrib["sc"])
        text += "\n" + self.ba_tostr(attrib["ba"])
        if "owari" in attrib:
            text += "\n" + self.owari(attrib["owari"])
        return text

    def agari(self, attrib):
        hai = list(map(int, attrib["hai"].split(",")))
        machi = int(attrib["machi"])
        ten = list(map(int, attrib["ten"].split(",")))
        who = int(attrib["who"])
        fromwho = int(attrib["fromWho"])
        yaku = list(map(int, attrib["yaku"].split(",")))
        yaku = zip(*[iter(yaku)] * 2)
        sc = attrib["sc"]
        m = list(map(int, attrib["m"].split(","))) if "m" in attrib else []

        dora = list(map(int, attrib["doraHai"].split(",")))
        ba = attrib["ba"]

        text = "ツモ " if who == fromwho else "ロン "
        text += self.game.player[who].name
        text += ("<-" + self.game.player[fromwho].name) \
            if who != fromwho else ""
        text += ' {0}順目'.format(len(self.player_mopai[who]))
        text += "\n"
        for h in hai:
            if machi != h:
                text += pstr(h)
        for f in m:
            text += " " + Fulou(f).pai
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
            return -1 if a < b else (0 if a == b else 1)
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
        text += "\n" + self.ba_tostr(ba) + "\n"
        text += self.sc_tostr(sc)
        if "owari" in attrib:
            text += "\n" + self.owari(attrib["owari"])
        return text

    def owari(self, data):
        text = "終局\n"
        text += self.sc_tostr(data, owari=True)
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
            print(game.go(int(child.attrib["type"])))
            print(game.type)
        elif (child.tag)[0:2] == "UN":
            print(game.un(child.attrib))
        elif (child.tag) == "TAIKYOKU":
            pass
        elif child.tag == "INIT":
            print(game.init(child.attrib))
        elif child.tag == "AGARI":
            print(game.agari(child.attrib))
        elif child.tag in {"DORA"}:
            #print(child.tag, child.attrib)
            pass
        elif child.tag == "REACH":
            #print(child.attrib)
            temp = game.reach(child.attrib)
            if temp != None:
                print(temp)
        elif (child.tag)[0] in {"T", "U", "V", "W"}:
            game.zimo(child.tag)
        elif (child.tag)[0] in {"D", "E", "F", "G"}:
            game.dapai(child.tag)
        elif child.tag == "N":
            print(game.naki(child.attrib))
        elif child.tag == "RYUUKYOKU":
            print(game.ryuukyoku(child.attrib))
        elif child.tag in {"SHUFFLE", "REACH", "BYE"}:
            pass
        else:
            print(child.tag, child.attrib)

    return


if __name__ == '__main__':
    download("2017042101gm-00c1-0000-4b052ac7")

# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pprint import pprint
#https://gist.github.com/nullpos/d6a10e1f4b1f906d8b6d
archive_url = 'http://e.mjv.jp/0/log/archived.cgi?'
plain_url = 'http://e.mjv.jp/0/log/plainfiles.cgi?'

def pai(num):
	hai =["一","二","三","四","五","六","七","八","九","①","②","③","④","⑤","⑥","⑦","⑧","⑨","1","2","3","4","5","6","7","8","9","東","南","西","北","白","發","中"]
	return hai[num>>2]
	

def zimo(tag):
	hito=chr(ord(tag[0])-19)+"さん"
	str=pai(int(tag[1:]))
	print(hito+"の自摸"+str)
def dapai(tag):
	hito=chr(ord(tag[0])-3)+"さん"
	str=pai(int(tag[1:]))
	print(hito+"の打牌"+str)
class Player:
	DAN=[
	"新人","９級","８級","７級","６級","５級","４級","３級","２級","１級",
	"初段","二段","三段","四段","五段","六段","七段","八段","九段","十段",
	"天鳳","RESERVED..."]
	def __init__(self,name):
		self.name=urllib.parse.unquote(name)
		
def fulou(val):
	if val&0x4:
		#順子
		t_ = val>>10
		t = floor(t_/3)
		r = t_%3
		if r==0:
			return pai(t<<2)+pai((t+1)<<2)+pai((t+2)<<2)
		elif r==1:
			return pai((t+1)<<2)+pai((t)<<2)+pai((t+2)<<2)
		elif r==2:
			return pai((t+2)<<2)+pai((t)<<2)+pai((t+1)<<2)
	elif val&0x8:
		#刻子
		t = floor((val>>9)/3)
		kui = val&0x3
		if kui==1:
			return pai(t<<2)+pai(t<<2)+"\"+pai(t<<2)
		elif kui==2:
			return pai(t<<2)+"\"+pai(t<<2)+pai(t<<2)
		elif kui==3:
			return "\"+pai(t<<2)+pai(t<<2)+pai(t<<2)
	elif val&0x10:
		#加槓
		t = floor((val>>9)/3)
		kui = val&0x3
		if kui==1:
			return pai(t<<2)+pai(t<<2)+"\\"+pai(t<<2)+"\\"+pai(t<<2)
		elif kui==2:
			return pai(t<<2)+"\\"+pai(t<<2)+"\\"+pai(t<<2)+pai(t<<2)
		elif kui==3:
			return "\\"+pai(t<<2)+"\\"+pai(t<<2)+pai(t<<2)+pai(t<<2)
	else:
		#明槓・あん槓
		t = (val>>10)
		kui = val&0x3
		if kui==1:
			return pai(t<<2)+pai(t<<2)+pai(t<<2)+"\\"+pai(t<<2)
		elif kui==2:
			return pai(t<<2)+"\\"+pai(t<<2)+pai(t<<2)+pai(t<<2)
		elif kui==3:
			return "\\"+pai(t<<2)+pai(t<<2)+pai(t<<2)+pai(t<<2)
		else:
			return pai(t<<2)+pai(t<<2)+pai(t<<2)+pai(t<<2)
			
class Game:
	def __init__(self):
		self.name = ""
		self.round = []

	def go(self,type):
		self.type = ""
		self.typecode = type
		if type&0x10:
			self.type+="三"
		if type&0xA0 == 0xA0:
			self.type += "鳳"
		elif type&0x20:
			self.type += "特"
		elif type&0x80:
			self.type += "上"
		else:
			self.type += "般"
		if type&8:
			self.type += "南"
		else:
			self.type += "東"
		if not(type&4):
			self.type += "喰"
		if not(type&2):
			self.type += "赤"
		if type&0x40:
			self.type += "速"
	def un(self,attrib):
		self.player = []
		self.player.append(Player(attrib["n0"]))
		self.player.append(Player(attrib["n1"]))
		self.player.append(Player(attrib["n2"]))
		if not(self.typecode&0x10):
			self.player.append(Player(attrib["n3"]))
	
	def init(self,attrib):
		seed = attrib["seed"].split(",")
		ten = attrib["ten"].split(",")
		if not(seed[0]==0 and seed[1]==0):
			self.round.append(self.current_round)
		self.current_round = Round(seed,ten)
	
	def agari(self,attrib):
		hai = attrib["hai"]
		
		m = attrib["m"]
		machi = attrib["machi"]
		ten = attrib["ten"]
		
		self.current_round.agari()
		
		
class Round:
	def __init__(self,seed,ten):
		self.seed = seed
		self.init_ten = ten
		
	def agari(self,who,)
	
	

def download(urlid):
	response = urllib.request.urlopen(archive_url+urlid)
	data = response.read()
	XmlData = data.decode('utf-8')
	if len(XmlData) < 10:
		response = urllib.request.urlopen(plain_url + urlid).read()
		data = response.read()
		XmlData = data.decode('utf-8')
	root = ET.fromstring(XmlData)
	game = Game()
	
	for child in root:
		#print(child.tag, child.attrib)
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
		elif (child.tag) in {"GO","DORA"}:
			print(child.tag,child.attrib)
		elif (child.tag)[0] in {"T","U","V","W"}:
			zimo(child.tag)
		elif (child.tag)[0] in {"D","E","F","G"}:
			dapai(child.tag)
		else:
			print(child.tag, child.attrib)
	return

if __name__ == '__main__':
	download("2016120723gm-0089-0000-6c96a657")
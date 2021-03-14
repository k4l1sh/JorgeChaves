import discord
import os
import tweepy
import re
import requests
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import ctypes
import ctypes.util

discord_token = os.environ['disctoken']
consumer_key = os.environ['twikey']
consumer_secret = os.environ['twisecret']
access_token = os.environ['twitoken']
access_token_secret = os.environ['twitokensecret']

limpeza = (
	('chat-10min', 600),
	('chat-24h', 86400)
	)
feed_twitter = (
	('genshin-impact', 'GenshinImpact'),
	('genshin-impact', 'Zeniiet'),
	('ashes-of-creation', 'AshesofCreation'),
	('cnn-international', 'cnni'),
	('nytimes-world', 'nytimesworld'),
	('bbc-world', 'BBCWorld'),
	('bitcoin', 'BTCTN'),
	('bbc-brasil', 'bbcbrasil'),
	('g1', 'g1'),
	('cnn-brasil', 'CNNBrasil')
	)

authT = tweepy.OAuthHandler(consumer_key, consumer_secret)
authT.set_access_token(access_token, access_token_secret)
apiT = tweepy.API(authT)

#client = discord.Client()
client = commands.Bot(command_prefix="!")

def filtro_urls(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]

async def enviar_mensagens_unicas(canal, texto, sourl=False):
	CanalH = client.get_channel(discord.utils.get(client.get_all_channels(), name=canal).id)
	marcador = 0
	mensagens = await CanalH.history(limit=300).flatten()
	texto_in = filtro_urls(texto)[0] if sourl else texto
	for msg in mensagens:
	   if texto_in in msg.content:
		   marcador += 1
	if marcador == 0:
	   await CanalH.send(texto)

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='news'))
	print('Bot is ready')
	limpar_mensagens.start(limpeza)
	tweeter_loop_get.start(feed_twitter)
	slow_news_get.start()
	fast_news_get.start()

@tasks.loop(seconds=60)
async def limpar_mensagens(canais):
	for canal, tempo in canais:
		Channel = client.get_channel(discord.utils.get(client.get_all_channels(), name=canal).id)
		for mensagem in await Channel.history(limit=1000).flatten():
			if not mensagem.author.bot and datetime.utcnow()-mensagem.created_at > timedelta(seconds=tempo):
				await mensagem.delete()

@tasks.loop(seconds=420)
async def tweeter_loop_get(feed):
	for canal, usuario in feed:
		feed = apiT.user_timeline(usuario, count=1, include_rts=False, exclude_replies=True, tweet_mode="extended")
		if len(feed) != 0:
        	    texto = feed[0].full_text
        	    for url in filtro_urls(texto):
        	           texto = texto.replace(url, "<"+url+">")
        	    await enviar_mensagens_unicas(canal, texto)

@tasks.loop(seconds=660)
async def fast_news_get():
	worldNews = BeautifulSoup(requests.get('https://old.reddit.com/r/worldnews/top/?t=day', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('a', {'data-event-action': 'title'})
	arsTechnica = BeautifulSoup(requests.get('https://arstechnica.com/', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('section', {'class': 'listing listing-top with-feature'})[0].findAll('li')
	for news in worldNews:
	    if ('alb.reddit.com' not in news['href']) and ('/user/' not in news['href']):
	        await enviar_mensagens_unicas('world-news', news.text+" <"+news['href']+">")
	for news in arsTechnica:
	    if 'abtest' not in news.find('h2').text:
	        await enviar_mensagens_unicas('ars-technica', "**"+news.find('h2').text+"** <"+news.find('a')['href']+">\n"+news.find('p').text, True)

@tasks.loop(seconds=7000)
async def slow_news_get():
	gamesSkid = BeautifulSoup(requests.get('https://www.skidrowreloaded.com/').content, 'html.parser').findAll('div', {'class': 'post'})
	gamesSteam = BeautifulSoup(requests.get('https://old.reddit.com/r/steamdeals/top/?sort=top&t=day', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('a', {'data-event-action': 'title'})
	newsLoL = BeautifulSoup(requests.get('https://br.leagueoflegends.com/pt-br/news/', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('li', {'class': 'style__ArticleItem-sc-8pxueq-5 bZBZqa'})
	natureNews = BeautifulSoup(requests.get('https://www.nature.com/news', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').find('section', {'class': 'section__top-new cleared'}).findAll('a', {'data-track': 'click'})
	gamesMetacritic = BeautifulSoup(requests.get('https://www.metacritic.com/browse/games/release-date/new-releases/pc/metascore?view=condensed', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('tr', {'class': 'expand_collapse'})
#	newsEsports = BeautifulSoup(requests.get('https://www.esports.com/en/news', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('div', {'class': 'container'})[3].findAll('a')
	for game in gamesSkid:
		await enviar_mensagens_unicas('skidrow-reloaded', game.find('a').text+": <"+game.find('a')['href']+">")
	for game in gamesSteam:
	    if ('alb.reddit.com' not in game['href']) and ('/user/' not in game['href']):
	        await enviar_mensagens_unicas('steam-deals', game.text+" <"+game['href']+">")
	for game in gamesMetacritic:
		await enviar_mensagens_unicas('metacritic-trends', "("+game.find('td', {'class': 'score'}).div.text+") **"+game.find('td', {'class': 'details'}).h3.text+"**. "+game.find('td', {'class': 'details'}).findAll('span')[3].text+" <https://www.metacritic.com"+game.find('td', {'class': 'details'}).find('a')['href']+">", True)
	for news in newsLoL:
	   hrefLoL = news.next['href']
	   if 'http' not in hrefLoL:
		   hrefLoL = "https://br.leagueoflegends.com"+hrefLoL
	   await enviar_mensagens_unicas('league-of-legends', "**"+news.find('h2').text+"** <"+hrefLoL+">\n"+news.find('p').text)
	for news in natureNews:
	   await enviar_mensagens_unicas('nature', news.find('h3').text.strip()+" <"+news['href']+">", True)
#	for news in newsEsports:
#	   await enviar_mensagens_unicas('esports', "("+news.find('div', {'class': 'relative w-full content-tile text-charcoal'}).findAll('div')[1].text+") **"+news.find('div', {'class': 'relative w-full content-tile text-charcoal'}).findAll('div')[2].text.strip()+"** <"+news['href']+">", True)

@client.command()
async def falajorge(ctx, arg):
	await ctx.send(arg)

def endSong(guild, path):
    os.remove(path)

@client.command()
async def p(ctx, arg):
	data = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vTH_cLTC9WWqvZaU_6MNuT1ReQvTp6nszF3rhzzpWzC78xm940Ykjo1_jcjByVbk47r2tR-FWpEUfRN/pub?gid=0&single=true&output=csv')
	if(data.COMANDO.isin([arg]).any()):
		path = data.MP3[data.loc[data.isin([arg]).any(axis=1)].index.tolist()[0]]
		voice_client = await ctx.author.voice.channel.connect()
		voice_client.play(discord.FFmpegPCMAudio(path), after=lambda x: endSong(ctx.message.guild.id, path))
		voice_client.source = discord.PCMVolumeTransformer(voice_client.source, 1)
		while voice_client.is_playing():
			await asyncio.sleep(1)
		else:
			await voice_client.disconnect()

client.run(discord_token)
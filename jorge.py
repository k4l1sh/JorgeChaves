import discord
import os
import tweepy
import re
import requests
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import ctypes
import ctypes.util

# chaves de API do discord e do twitter (para guardar nas config vars do heroku ou outro servidor de hospedagem)
discord_token = os.environ['disctoken']
consumer_key = os.environ['twikey']
consumer_secret = os.environ['twisecret']
access_token = os.environ['twitoken']
access_token_secret = os.environ['twitokensecret']

# (canal do discord, tempo em segundos) para executar uma limpeza rotineira de mensagens
limpeza = (
	('chat-10min', 600),
	('chat-24h', 86400),
	('bot-commands', 1800)
	)

# (canal do discord, perfil do twitter) para capturar os ultimos tweets
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

# canais do discord com um scraper das comunidades do reddit
canal_steam_deals = 'steam-deals'
canal_world_news = 'world-news'

# canais do discord com um scraper exclusivo
canal_metacritic_trends = 'metacritic-trends'
canal_noticias_lol = 'league-of-legends'
canal_nature = 'nature'
canal_ars_technica = 'ars-technica'

# limite de tempo para o bot permanecer tocando um instant sound
music_maximum_time = 10



authT = tweepy.OAuthHandler(consumer_key, consumer_secret)
authT.set_access_token(access_token, access_token_secret)
apiT = tweepy.API(authT)

client = commands.Bot(command_prefix="!")

# filtro de urls para evitar o envio de embeds
def filtro_urls(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]

# evitar mensagens de dados repetidos
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

# ativar a limpeza, o scraping de dados e o status do bot
@client.event
async def on_ready():
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='news'))
	print('Bot funcionando')
	limpar_mensagens.start(limpeza)
	tweeter_loop_get.start(feed_twitter)
	slow_news_get.start()
	fast_news_get.start()

# polling de 1 minuto para limpeza
@tasks.loop(seconds=60)
async def limpar_mensagens(canais):
	for canal, tempo in canais:
		if(discord.utils.get(client.get_all_channels(), name=canal) is not None):
			Channel = client.get_channel(discord.utils.get(client.get_all_channels(), name=canal).id)
			for mensagem in await Channel.history(limit=1000).flatten():
				if not mensagem.author.bot and datetime.utcnow()-mensagem.created_at > timedelta(seconds=tempo):
					await mensagem.delete()

# polling de 7 minutos para scraping do twitter
@tasks.loop(seconds=420)
async def tweeter_loop_get(feed):
	for canal, usuario in feed:
		if(discord.utils.get(client.get_all_channels(), name=canal) is not None):
			feed = apiT.user_timeline(usuario, count=1, include_rts=False, exclude_replies=True, tweet_mode="extended")
			if len(feed) != 0:
					texto = feed[0].full_text
					for url in filtro_urls(texto):
						texto = texto.replace(url, "<"+url+">")
					await enviar_mensagens_unicas(canal, texto)

# polling de 11 minutos para scraping de dados transientes
@tasks.loop(seconds=660)
async def fast_news_get():
	if(discord.utils.get(client.get_all_channels(), name=canal_world_news) is not None):
		worldNews = BeautifulSoup(requests.get('https://old.reddit.com/r/worldnews/top/?t=day', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('a', {'data-event-action': 'title'})
		for news in worldNews:
			if ('alb.reddit.com' not in news['href']) and ('/user/' not in news['href']):
				await enviar_mensagens_unicas(canal_world_news, news.text+" <"+news['href']+">")
	if(discord.utils.get(client.get_all_channels(), name=canal_ars_technica) is not None):
		arsTechnica = BeautifulSoup(requests.get('https://arstechnica.com/', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('section', {'class': 'listing listing-top with-feature'})[0].findAll('li')
		for news in arsTechnica:
			if 'abtest' not in news.find('h2').text:
				await enviar_mensagens_unicas(canal_ars_technica, "**"+news.find('h2').text+"** <"+news.find('a')['href']+">\n"+news.find('p').text, True)

# polling de ~117 minutos para scraping de dados duradouros
@tasks.loop(seconds=7000)
async def slow_news_get():
	if(discord.utils.get(client.get_all_channels(), name=canal_steam_deals) is not None):
		gamesSteam = BeautifulSoup(requests.get('https://old.reddit.com/r/steamdeals/top/?sort=top&t=day', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('a', {'data-event-action': 'title'})
		for game in gamesSteam:
			if ('alb.reddit.com' not in game['href']) and ('/user/' not in game['href']):
				await enviar_mensagens_unicas(canal_steam_deals, game.text+" <"+game['href']+">")
	if(discord.utils.get(client.get_all_channels(), name=canal_metacritic_trends) is not None):
		gamesMetacritic = BeautifulSoup(requests.get('https://www.metacritic.com/browse/games/release-date/new-releases/pc/metascore?view=condensed', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('tr', {'class': 'expand_collapse'})
		for game in gamesMetacritic:
			await enviar_mensagens_unicas(canal_metacritic_trends, "("+game.find('td', {'class': 'score'}).div.text+") **"+game.find('td', {'class': 'details'}).h3.text+"**. "+game.find('td', {'class': 'details'}).findAll('span')[3].text+" <https://www.metacritic.com"+game.find('td', {'class': 'details'}).find('a')['href']+">", True)
		newsLoL = BeautifulSoup(requests.get('https://br.leagueoflegends.com/pt-br/news/', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').findAll('li', {'class': 'style__ArticleItem-sc-8pxueq-5 bZBZqa'})
	if(discord.utils.get(client.get_all_channels(), name=canal_noticias_lol) is not None):
		for news in newsLoL:
			hrefLoL = news.next['href']
			if 'http' not in hrefLoL:
				hrefLoL = "https://br.leagueoflegends.com"+hrefLoL
			await enviar_mensagens_unicas(canal_noticias_lol, "**"+news.find('h2').text+"** <"+hrefLoL+">\n"+news.find('p').text)
	if(discord.utils.get(client.get_all_channels(), name=canal_nature) is not None):
		natureNews = BeautifulSoup(requests.get('https://www.nature.com/news', headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser').find('section', {'class': 'section__top-new cleared'}).findAll('a', {'data-track': 'click'})
		for news in natureNews:
			await enviar_mensagens_unicas(canal_nature, news.find('h3').text.strip()+" <"+news['href']+">", True)

# adiciona um emoji a cada mensagem no canal de memes
@client.event
async def on_message(message):
	if 'memes' == str(message.channel):
		await message.add_reaction("😂")
	await client.process_commands(message)

# envia a mensagem como bot, para evitar limpeza
@client.command(pass_context=True)
async def falajorge(ctx, arg):
	await ctx.send(arg)
	await ctx.message.delete()

# ativa o comando !p para ouvir instant sounds utilizando uma planilha do google sheets como CMS
@client.command(pass_context=True)
async def p(ctx, arg):
	data = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vTH_cLTC9WWqvZaU_6MNuT1ReQvTp6nszF3rhzzpWzC78xm940Ykjo1_jcjByVbk47r2tR-FWpEUfRN/pub?gid=0&single=true&output=csv')
	if(data.COMANDO.isin([arg]).any()):
		await ctx.message.add_reaction("✔️")
		path = data.MP3[data.loc[data.isin([arg]).any(axis=1)].index.tolist()[0]]
		voice_client = await ctx.author.voice.channel.connect()
		voice_client.play(discord.FFmpegPCMAudio(path))
		voice_client.source = discord.PCMVolumeTransformer(voice_client.source, 1)
		s = 0
		while not s >= music_maximum_time:
			await asyncio.sleep(1)
			s += 1
		else:
			await voice_client.disconnect()
			await ctx.message.delete()

client.run(discord_token)
# TODO: on_join eventek


import discord
import asyncio
import json
from discord.ext import commands
import os
import logging
import sqlalchemy as sql
from threading import Thread, Event, Timer

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

default_prefix = "!"


import traceback

try:
	with open("config.json", encoding="utf-8") as f:
		config = json.loads(f.read())
		for k in ["token", "dbip", "dbname", "dbuser", "dbpass"]:
			a = config[k]
except:
	print("VALAMI NEM JÓ A config.json FÁJLBAN:")
	traceback.print_exc()
	exit()

TOKEN = config["token"]

sqlEngine = sql.create_engine("mysql+pymysql://"+config["dbuser"]+":"+config["dbpass"]+"@"+config["dbip"]+":3306/"+config["dbname"], pool_pre_ping=True)
sqlConn = sqlEngine.connect()
sqlMetadata = sql.MetaData(sqlEngine)

class sqlTablesHolder():
	concepts = sql.Table("concepts", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('message_id', sql.String(32)), sql.Column('channel_id', sql.String(32)), sql.Column('guild_id', sql.String(32)), sql.Column('title', sql.String(1024)), sql.Column('desc', sql.String(2048)), sql.Column('author_id', sql.String(32)), sql.Column('votes', sql.Integer), sql.Column('updated', sql.dialects.mysql.TINYINT(1), nullable=False, server_default="0"))

sqlTables = sqlTablesHolder()

sqlMetadata.create_all()

attachedMessages = {}

toplistaData = {"message_id":"560878684282814504", "channel_id":"560145378960474143", "guild_id":"488723895394893825","message":None}




bot = commands.Bot(command_prefix=default_prefix)

bot.remove_command('help')
	
@bot.event
async def on_ready():
	await bot.change_presence(activity=discord.Activity(name='Ötletek',type=3))
	#await bot.change_presence(game=discord.Game(name='my game'))
	try:
		toplistaData["message"] = await bot.get_channel(int(toplistaData["channel_id"])).fetch_message(int(toplistaData["message_id"]))
	except discord.NotFound:
		print("\n\n\n"+29*"=")
		print("| TOPLIST MESSAGE NOT FOUND |")
		print(29*"=","\n\n\n")
	print("Everything's all ready to go~")
	
@bot.event
async def on_message(message):
	# if message.guild:
		# print("[("+message.guild.name+") "+message.channel.name+" : "+message.author.name+"] "+message.content)
	# else:
		# print("["+message.author.name+"] "+message.content)
	await bot.process_commands(message)
	

@bot.event
async def on_raw_message_delete(payload):
	sqlConn.execute(sqlTables.concepts.delete().where(sqlTables.concepts.c.message_id == payload.message_id))
	await update_toplist(toplistaData["message"])
		
@bot.event
async def on_raw_reaction_add(payload):
	if payload.user_id != bot.user.id:
		try:
			message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
		except:
			pass
		else:
			if payload.emoji.is_unicode_emoji() and payload.emoji.name == "\U0001F5D1" and message.author.id == payload.user_id: # :wastebin:
				if attachedMessages.get(str(payload.message_id)):
					for m in attachedMessages.get(str(payload.message_id)):
						try:
							await m.delete()
						except:
							pass
					del attachedMessages[str(payload.message_id)]
			elif payload.emoji.is_unicode_emoji() and payload.emoji.name == "\U00002705": # :white_check_mark:
				sqlConn.execute(sqlTables.concepts.update().where(sqlTables.concepts.c.message_id == payload.message_id).values(votes=message.reactions[0].count))
				await update_toplist(toplistaData["message"])
		


@bot.event
async def on_raw_reaction_remove(payload):
	if payload.user_id != bot.user.id:
		try:
			message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
		except:
			pass
		else:
			if len(message.reactions) > 0 and payload.emoji.is_unicode_emoji() and payload.emoji.name == "\U00002705": # :white_check_mark:
				sqlConn.execute(sqlTables.concepts.update().where(sqlTables.concepts.c.message_id == payload.message_id).values(votes=message.reactions[0].count))
				await update_toplist(toplistaData["message"])
	
async def update_toplist(message):
	top = sqlConn.execute(sqlTables.concepts.select().order_by(sqlTables.concepts.c.votes.desc()).limit(10)).fetchmany(10)
	#print(top)
	embed = discord.Embed(
		color=0xf3b221, 
		description="Legtöbb szavazattal rendelkező koncepciók",
		title="Toplista")
	# embed.set_author(name="Andruida")
	loops = 0
	topstr = ""
	for item in top:
		if loops < 10:
			loops += 1
			#embed.add_field(name=str(loops)+". "+item.title, value=item.desc, inline=False)
			#embed.description += str(loops)+". "+item.title+"\n"
			if len(item.title) < 50:
				topstr += str(loops)+". "+item.title+" - "+str(item.votes)+" szavazat\n"
			else:
				topstr += str(loops)+". "+item.title[:50]+"...- "+str(item.votes)+" szavazat\n"
	embed.add_field(name="Top 10:", value=topstr if len(topstr) > 0 else "Nincs koncepció", inline=False)
	try:
		await message.edit(embed=embed)
	except:
		print("Editing toplist failed")


	
@bot.command()
#@commands.has_permissions(administrator=True)
@commands.check(lambda ctx: str(ctx.message.channel.id) == "560146414085210122")
@commands.has_any_role(488726625970814977, 488724886366322698)
async def register(ctx, member='', title='', *, desc=''):
	if member=='' or title == '' or desc == '' or len(ctx.message.mentions) != 1:
		embed = discord.Embed(
			color=0xf3b221, 
			description="Hibásan használtad a parancsot",
			title="Szintaktikai hiba")
		embed.add_field(name="Syntax:", value=bot.command_prefix+"register <alkotó> <cím> <leírás>", inline=False)
		embed.add_field(name="Alkotó", value="A koncepcíó alkotója, jelöld meg")
		embed.add_field(name="Név", value="A koncepcíó lényege, címe. Ha több szóból áll tedd idézőjelek közé.")
		embed.add_field(name="Leírás", value="A koncepció hosszú leírása\nHasználhatsz benne Discord-os (Markdown) formázásokat is")
		answer = await ctx.send(embed=embed)
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
		# await ctx.message.add_reaction("\U0000274C") # :x:
	else:
		try:
			await ctx.message.delete()
		except:
			pass
		member = ctx.message.mentions[0]
		embed = discord.Embed(
			color=0xf3b221, 
			description=desc,
			title=title)
		embed.set_footer(text=str(member.display_name) if member.display_name == member.name else str(member.name) + " ("+str(member.display_name)+")", icon_url=member.avatar_url)
		answer = await ctx.send(embed=embed)
		sqlConn.execute(sqlTables.concepts.insert().values(message_id=answer.id, channel_id=answer.channel.id, guild_id=answer.guild.id, votes=1, title=title, desc=desc, author_id=member.id))
		await answer.add_reaction("\U00002705")
		await update_toplist(toplistaData["message"])



@bot.command()
async def top(ctx, num=1):
	r = sqlConn.execute(sqlTables.concepts.select().order_by(sqlTables.concepts.c.votes.desc()).offset(num-1).limit(1)).fetchone()
	if r:
		# try:
			# await ctx.message.delete()
		# except:
			# pass
		try:
			member = bot.get_guild(int(r.guild_id)).get_member(int(r.author_id))
		except:
			member = ctx.message.author
		embed = discord.Embed(
			color=0xf3b221, 
			description=r.desc,
			title=r.title)
		embed.set_footer(text=str(member.display_name) if member.display_name == member.name else str(member.name) + " ("+str(member.display_name)+")", icon_url=member.avatar_url)
		answer = await ctx.send(embed=embed)
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	else:
		answer = await ctx.send("Nincs egyező mező")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]


		
@bot.command(aliases=["toplist"])
async def toplista(ctx):
	# try:
		# await ctx.message.delete()
	# except:
		# pass
	top = sqlConn.execute(sqlTables.concepts.select().order_by(sqlTables.concepts.c.votes.desc()).limit(10)).fetchmany(10)
	embed = discord.Embed(
		color=0xf3b221, 
		description="Legtöbb szavazattal rendelkező koncepciók",
		title="Toplista")
	# embed.set_author(name="Andruida")
	loops = 0
	topstr = ""
	for item in top:
		if loops < 10:
			loops += 1
			#embed.add_field(name=str(loops)+". "+item.title, value=item.desc, inline=False)
			#embed.description += str(loops)+". "+item.title+"\n"
			if len(item.title) < 50:
				topstr += str(loops)+". "+item.title+" - "+str(item.votes)+" szavazat\n"
			else:
				topstr += str(loops)+". "+item.title[:50]+"...- "+str(item.votes)+" szavazat\n"
	embed.add_field(name="Top 10:", value=topstr if len(topstr) > 0 else "Nincs koncepció", inline=False)
	# embed.add_field(name="field4", value="field4 értéke", inline=True)
	answer = await ctx.send(embed=embed)
	await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
	attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
#

@bot.group()
async def vote(ctx):
	if ctx.invoked_subcommand is None:
		try:
			await ctx.message.delete()
		except:
			pass
		await ctx.send("Használat: `!vote map [idő]`", delete_after=10.0)

@vote.command(name="map")
@commands.has_any_role(488726625970814977, 488724886366322698)
async def votemap(ctx, time="120"):
	if not str(time).isdigit() or int(time) > 3600:
		time = 120
	else:
		time = int(time)
	try:
		await ctx.message.delete()
	except:
		pass
	embed = discord.Embed(
		color=0xf3b221, 
		description="**A pályaválasztás elkezdődött!** - "+str(time)+" másodperc van hátra.\n\n*Reakciókkal tudod leadni a szavazatodat.*\n:white_circle: Erangel\n:red_circle: Miramar\n:large_blue_circle: Sanhok\n:black_circle: Vikendi",
		title="Map választás")
	answer = await ctx.send(embed=embed)
	await answer.add_reaction("\U000026AA") # :white_circle:
	await answer.add_reaction("\U0001F534") # :red_circle:
	await answer.add_reaction("\U0001F535") # :large_blue_circle:
	await answer.add_reaction("\U000026AB") # :black_circle:
	#attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	await asyncio.sleep(time)
	try:
		tracked = await ctx.fetch_message(answer.id)
		await answer.delete()
	except:
		pass
	else:
		maps = [
			{"name": "Erangel", "count":discord.utils.get(tracked.reactions, emoji="\U000026AA").count - 1, "emoji":":white_circle:"},
			{"name": "Miramar", "count":discord.utils.get(tracked.reactions, emoji="\U0001F534").count -1, "emoji":":red_circle:"},
			{"name": "Sanhok", "count":discord.utils.get(tracked.reactions, emoji="\U0001F535").count - 1, "emoji":":large_blue_circle:"},
			{"name": "Vikendi", "count":discord.utils.get(tracked.reactions, emoji="\U000026AB").count -1, "emoji":":black_circle:"}
		]
		winner = max(maps, key=lambda x: x["count"])
		embed = discord.Embed(
			color=0xf3b221,
			title="A szavazás véget ért")
		embed.add_field(name="Eredmények:", value=":white_circle: Erangel - {0} szavazat\n:red_circle: Miramar - {1} szavazat\n:large_blue_circle: Sanhok - {2} szavazat\n:black_circle: Vikendi - {3} szavazat".format(str(maps[0]["count"]), str(maps[1]["count"]), str(maps[2]["count"]), str(maps[3]["count"])), inline=False)
		embed.add_field(name="Győztes:", value="{2} **{0}** - {1} szavazattal".format(winner["name"], str(winner["count"]), winner["emoji"]), inline=False)
		await ctx.send(embed=embed, delete_after=300.0)

@vote.command(name="team")
@commands.has_any_role(488726625970814977, 488724886366322698)
async def voteteam(ctx, time="120"):
	if not str(time).isdigit() or int(time) > 3600:
		time = 120
	else:
		time = int(time)
	try:
		await ctx.message.delete()
	except:
		pass
	embed = discord.Embed(
		color=0xf3b221, 
		description="**A csapat méretének választása elkezdődött!** - "+str(time)+" másodperc van hátra.\n\n*Reakciókkal tudod leadni a szavazatodat.*\n:white_circle: Duo\n:red_circle: Trio\n:large_blue_circle: Squad\n:black_circle: 8 Man Squad",
		title="Map választás")
	answer = await ctx.send(embed=embed)
	await answer.add_reaction("\U000026AA") # :white_circle:
	await answer.add_reaction("\U0001F534") # :red_circle:
	await answer.add_reaction("\U0001F535") # :large_blue_circle:
	await answer.add_reaction("\U000026AB") # :black_circle:
	#attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	await asyncio.sleep(time)
	try:
		tracked = await ctx.fetch_message(answer.id)
		await answer.delete()
	except:
		pass
	else:
		maps = [
			{"name": "Duo", "count":discord.utils.get(tracked.reactions, emoji="\U000026AA").count - 1, "emoji":":white_circle:"},
			{"name": "Trio", "count":discord.utils.get(tracked.reactions, emoji="\U0001F534").count -1, "emoji":":red_circle:"},
			{"name": "Squad", "count":discord.utils.get(tracked.reactions, emoji="\U0001F535").count - 1, "emoji":":large_blue_circle:"},
			{"name": "8 Man Squad", "count":discord.utils.get(tracked.reactions, emoji="\U000026AB").count -1, "emoji":":black_circle:"}
		]
		winner = max(maps, key=lambda x: x["count"])
		embed = discord.Embed(
			color=0xf3b221,
			title="A szavazás véget ért")
		embed.add_field(name="Eredmények:", value=":white_circle: Duo - {0} szavazat\n:red_circle: Trio - {1} szavazat\n:large_blue_circle: Squad - {2} szavazat\n:black_circle: 8 Man Squad - {3} szavazat".format(str(maps[0]["count"]), str(maps[1]["count"]), str(maps[2]["count"]), str(maps[3]["count"])), inline=False)
		embed.add_field(name="Győztes:", value="{2} **{0}** - {1} szavazattal".format(winner["name"], str(winner["count"]), winner["emoji"]), inline=False)
		await ctx.send(embed=embed, delete_after=300.0)


@bot.command()
#@commands.has_permissions(administrator=True)
@commands.has_any_role(488726625970814977, 488724886366322698)
async def update(ctx):
	# try:
		# await ctx.message.delete()
	# except:
		# pass
	r = sqlConn.execute(sqlTables.concepts.select().where(sqlTables.concepts.c.updated == 1))
	updatedMessages = {"failed":[], "succeeded":[], "reasons":[]}
	for m in r:
		try:
			message = await bot.get_channel(int(m.channel_id)).fetch_message(int(m.message_id))
		except:
			updatedMessages["failed"].append(m)
			updatedMessages["reasons"].append("Nem található üzenet")
		else:
			try:
				member = bot.get_guild(int(m.guild_id)).get_member(int(m.author_id))
			except:
				member = None
			embed = discord.Embed(
				color=0xf3b221, 
				description=m.desc,
				title=m.title)
			if member:
				embed.set_footer(text=str(member.display_name) if member.display_name == member.name else str(member.name) + " ("+str(member.display_name)+")", icon_url=member.avatar_url)
			else:
				embed.set_footer(text="Névtelen", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
			try:
				await message.edit(embed=embed)
			except:
				updatedMessages["failed"].append(m)
				updatedMessages["reasons"].append("Sikertelen szerkesztés")
			else:
				updatedMessages["succeeded"].append(m)
	embed = discord.Embed(
		color=0xf3b221, 
		title="Módosított koncepciók")
	successStr = ""
	failStr = ""
	for success in updatedMessages["succeeded"]:
		sqlConn.execute(sqlTables.concepts.update().where(sqlTables.concepts.c.id == success.id).values(updated=0))
		successStr += "ID: {0}, Cím: {1}\n".format(success.id, success.title)
	for i in range(len(updatedMessages["failed"])):
		failed = updatedMessages["failed"][i]
		failStr += "ID: {0}, Cím: {1}, Oka: {2}\n".format(failed.id, failed.title, updatedMessages["reasons"][i])
	embed.add_field(name="Sikeresen módosult", value=successStr if len(successStr) > 0 else "Nem módosult semmi", inline=False)
	embed.add_field(name="Sikertelen:", value=failStr if len(failStr) > 0 else "Nincs hiba", inline=False)
	answer = await ctx.send(embed=embed)
	await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
	attachedMessages[str(ctx.message.id)] = [ctx.message, answer]


bot.run(TOKEN)

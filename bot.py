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

sqlEngine = sql.create_engine("sqlite:///botdata.sqlite3")
sqlConn = sqlEngine.connect()
sqlMetadata = sql.MetaData(sqlEngine)

class sqlTablesHolder():
	concepts = sql.Table("concepts", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('message_id', sql.String), sql.Column('channel_id', sql.String), sql.Column('guild_id', sql.String), sql.Column('title', sql.String), sql.Column('desc', sql.String), sql.Column('author_id', sql.String), sql.Column('votes', sql.Integer))

sqlTables = sqlTablesHolder()

sqlMetadata.create_all()

attachedMessages = {}

toplistaData = {"message_id":"560878684282814504", "channel_id":"560145378960474143", "guild_id":"488723895394893825","message":None}



# class CheckVotes(Thread):
	# def __init__(self, event):
		# Thread.__init__(self)
		# self.stopped = event

	# def run(self):
		# while not self.stopped.wait(5):
			# sqlEngine = sql.create_engine("sqlite:///botdata.sqlite3")
			# sqlConn = sqlEngine.connect()
			# sqlMetadata = sql.MetaData(sqlEngine)

			# class sqlTablesHolder():
				# concepts = sql.Table("concepts", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('message_id', sql.String), sql.Column('channel_id', sql.String), sql.Column('guild_id', sql.String), sql.Column('votes', sql.Integer))

			# sqlTables = sqlTablesHolder()

			# sqlMetadata.create_all()
			# r = sqlConn.execute(sqlTables.concepts.select())
			# for row in r:
				# try:
					# print(row.channel_id)
					# m = bot.get_guild(row.guild_id).get_channel(row.channel_id).fetch_message(row.message_id)
					# print(m)
				# except (discord.NotFound):#, AttributeError):
					# sqlConn.execute(sqlTables.concepts.delete().where(sqlTables.concepts.c.message_id == row.message_id).where(sqlTables.concepts.c.channel_id == row.channel_id))
					# print("Invalid message deleted")
			# sqlConn.close()

# vote_stopper = Event()
# vote_checker = CheckVotes(vote_stopper)



TOKEN = ""
try:
	with open("key.txt") as f:
		try:
			TOKEN = f.read()
		except:
			print(27*"=")
			raise(" Can't access key.txt file")
			print(27*"=")
			exit()
except:
	print(23*"=")
	print(" NO key.txt FILE FOUND")
	print(23*"=")
	exit()


bot = commands.Bot(command_prefix=default_prefix)

bot.remove_command('help')
	
@bot.event
async def on_ready():
	await bot.change_presence(activity=discord.Activity(name='Ötletek',type=3))
	#await bot.change_presence(game=discord.Game(name='my game'))
	# vote_checker.start()
	try:
		toplistaData["message"] = await bot.get_channel(int(toplistaData["channel_id"])).fetch_message(int(toplistaData["message_id"]))
	except discord.NotFound:
		print("\n\n\n"+29*"=")
		print("| TOPLIST MESSAGE NOT FOUND |")
		print(29*"=","\n\n\n")
	print("Everything's all ready to go~")
	
@bot.event
async def on_message(message):
	if message.guild:
		print("[("+message.guild.name+") "+message.channel.name+" : "+message.author.name+"] "+message.content)
	else:
		print("["+message.author.name+"] "+message.content)
	await bot.process_commands(message)
	
# @bot.event
# async def on_reaction_add(reaction, user):
	# if reaction.emoji == "\U00002705":
		# print(reaction.count)

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
		
	#print(message.reactions[0].count)


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
	top = sqlConn.execute(sqlTables.concepts.select().order_by(sqlTables.concepts.c.votes.desc()).limit(10)).fetchmany(-1)
	#top = sorted(r, reverse=True, key=lambda x: x.votes)
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
			if len(item.title) < 60:
				topstr += str(loops)+". "+item.title+"\n"
			else:
				topstr += str(loops)+". "+item.title[:60]+"...\n"
	embed.add_field(name="Top 10:", value=topstr, inline=False)
	# embed.add_field(name="field4", value="field4 értéke", inline=True)
	try:
		await message.edit(embed=embed)
	except:
		print("Editing toplist failed")


# @bot.event
# async def on_reaction_remove(reaction, user):
	# if reaction.emoji == "\U00002705":
		# print(reaction.count)
	
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
		#embed.set_footer(text=str(ctx.message.author.display_name) if ctx.message.author.display_name == ctx.message.author.name else str(ctx.message.author.name) + " ("+str(ctx.message.author.display_name)+")", icon_url=ctx.message.author.avatar_url)
		# embed.set_author(name="Andruida")
		embed.add_field(name="Syntax:", value=bot.command_prefix+"register <alkotó> <cím> <leírás>", inline=False)
		embed.add_field(name="Alkotó", value="A koncepcíó alkotója, jelöld meg")
		embed.add_field(name="Név", value="A koncepcíó lényege, címe. Ha több szóból áll tedd idézőjelek közé.")
		embed.add_field(name="Leírás", value="A koncepció hosszú leírása\nHasználhatsz benne Discord-os (Markdown) formázásokat is")
		# embed.add_field(name="field3", value="field3 értéke", inline=False)
		# embed.add_field(name="field4", value="field4 értéke", inline=True)
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
		# embed.set_author(name="Andruida")
		# embed.add_field(name="field1", value="field1 értéke", inline=True)
		# embed.add_field(name="field2", value="field2 értéke", inline=False)
		# embed.add_field(name="field3", value="field3 értéke", inline=False)
		# embed.add_field(name="field4", value="field4 értéke", inline=True)
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
		# embed.set_author(name="Andruida")
		# embed.add_field(name="field1", value="field1 értéke", inline=True)
		# embed.add_field(name="field2", value="field2 értéke", inline=False)
		# embed.add_field(name="field3", value="field3 értéke", inline=False)
		# embed.add_field(name="field4", value="field4 értéke", inline=True)
		answer = await ctx.send(embed=embed)
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	else:
		answer = await ctx.send("Nincs egyező mező")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
		
@bot.command()
async def toplista(ctx):
	# try:
		# await ctx.message.delete()
	# except:
		# pass
	top = sqlConn.execute(sqlTables.concepts.select().order_by(sqlTables.concepts.c.votes.desc()).limit(10)).fetchmany(-1)
	#top = sorted(r, reverse=True, key=lambda x: x.votes)
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
			if len(item.title) < 60:
				topstr += str(loops)+". "+item.title+"\n"
			else:
				topstr += str(loops)+". "+item.title[:60]+"...\n"
	embed.add_field(name="Top 10:", value=topstr, inline=False)
	# embed.add_field(name="field4", value="field4 értéke", inline=True)
	answer = await ctx.send(embed=embed)
	await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
	attachedMessages[str(ctx.message.id)] = [ctx.message, answer]

bot.run(TOKEN)
# vote_stopper.set()
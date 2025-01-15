import discord
from discord.ext import commands
from discord import app_commands
from siegeapi import Auth
import asyncio
import os
from typing import Literal
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import json


load_dotenv(".env")


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)


with open("details/data.json", "r") as targets:
    data = json.load(targets)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')
    asyncio.create_task(track_all_players())


@bot.hybrid_command()
async def generalstats(uid: str, ctx):

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    player = await auth.get_player(uid=uid)

    await player.load_persona()
    
    if not player.persona.enabled:
        embed = discord.Embed(title=player.name, description=f"General Stats of {player.name}", color=0x00ff00)
    else:
        embed = discord.Embed(title=f"{player.name} ({player.persona.nickname})", description=f"General Stats of {player.name}", color=0x00ff00)

    embed.set_thumbnail(url=player.profile_pic_url_256)

    await player.load_playtime()
    embed.add_field(name="Level", value=player.level, inline=False)
    embed.add_field(name="Total Time Played (hours)", value=f"Total Playtime: {player.playtime.total_playtime/3600:,.0f}", inline=False)

    await player.load_progress()
    embed.add_field(name="XP", value=player.xp, inline=False)
    embed.add_field(name="Total XP", value=player.total_xp, inline=False)
    embed.add_field(name="Level", value=player.level, inline=False)
    embed.add_field(name="XP to level up", value=player.xp_to_level_up, inline=False)

    await ctx.send(embed=embed)
    await auth.close()




async def track(uid: str, discordIds: list):
    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    player = await auth.get_player(uid=uid)

    print(f"Name: {player.name}")

    await player.load_persona()
    if not player.persona.enabled:
        print(player.name)
    else:
        print(f"{player.name} ({player.persona.nickname})")
    print(f"Profile pic URL: {player.profile_pic_url}")

    await player.load_ranked_v2()
    print(f"Ranked Points: {player.ranked_profile.rank_points}")
    print(f"Rank: {player.ranked_profile.rank}")

    await player.load_playtime()
    print(f"{player.name} ({player.level})")

    await player.load_progress()
    print(f"XP: {player.xp}")
    print(f"Total XP: {player.total_xp}")
    print(f"Level: {player.level}")
    print(f"XP to level up: {player.xp_to_level_up}")

    await auth.close()


async def track_all_players():
    for player in data["players"]:
        await track(uid=player["ubiID"], discordIds=[reciever["discordID"] for reciever in data["recievers"] if reciever["user"] == player["name"]])


asyncio.get_event_loop().run_until_complete(track_all_players())
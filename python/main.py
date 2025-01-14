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

async def siege_track():
    while True:
        for target in data["players"]:
            auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
            player = await auth.get_player(uid=target["ubiID"])
            await player.load_ranked_v2()
            print(f"Name: {player.name}")
            print(f"Profile pic URL: {player.profile_pic_url}")
            print(f"Ranked Points: {player.ranked_profile.rank_points}")
            print(f"Rank: {player.ranked_profile.rank}")
            await auth.close()
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')
    asyncio.create_task(siege_track())


async def track(uid: str, discordIds: list):
    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    player = await auth.get_player(uid=uid)

    print(f"Name: {player.name}")
    print(f"Profile pic URL: {player.profile_pic_url}")

    await player.load_ranked_v2()
    print(f"Ranked Points: {player.ranked_profile.rank_points}")
    print(f"Rank: {player.ranked_profile.rank}")

    await auth.close()

async def track_all_players():
    for player in data["players"]:
        await track(uid=player["ubiID"], discordIds=[reciever["discordID"] for reciever in data["recievers"] if reciever["user"] == player["name"]])

asyncio.get_event_loop().run_until_complete(track_all_players())
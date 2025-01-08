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

with open("data.json", "r") as targets:
    data = json.load(targets)

async def siege_track():
    ubiIDs = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')
    asyncio.create_task(siege_track())

async def run():
    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    player = await auth.get_player(name="That9464")

    print(f"Name: {player.name}")
    print(f"Profile pic URL: {player.profile_pic_url}")

    await player.load_ranked_v2()
    print(f"Ranked Points: {player.ranked_profile.rank_points}")
    print(f"Rank: {player.ranked_profile.rank}")

    await auth.close()
    
asyncio.get_event_loop().run_until_complete(run())
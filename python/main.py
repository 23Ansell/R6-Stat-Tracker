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
async def generalstats(ctx, name: str):

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    player = await auth.get_player(name)

    await player.load_persona()
    
    if not player.persona.enabled:
        embed = discord.Embed(title=player.name, description=f"General Stats of {player.name}", color=0x00ff00)
    else:
        embed = discord.Embed(title=f"{player.name} ({player.persona.nickname})", description=f"General Stats of {player.name}", color=0x00ff00)

    embed.set_thumbnail(url=player.profile_pic_url_256)

    await player.load_playtime()
    embed.add_field(name="Level", value=player.level, inline=False)
    embed.add_field(name="Total Time Played (hours)", value=f"Total Playtime: {player.total_time_played/3600:,.0f}", inline=False)

    await player.load_progress()
    embed.add_field(name="XP", value=player.xp, inline=False)
    embed.add_field(name="Total XP", value=player.total_xp, inline=False)
    embed.add_field(name="Level", value=player.level, inline=False)
    embed.add_field(name="XP to level up", value=player.xp_to_level_up, inline=False)

    await ctx.send(embed=embed)
    await auth.close()


@bot.hybrid_command()
async def rankedstats(ctx, name: str):

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    player = await auth.get_player(name)


    await player.load_persona()
    
    if not player.persona.enabled:
        embed = discord.Embed(title=player.name, description=f"General Stats of {player.name}", color=0x00ff00)
    else:
        embed = discord.Embed(title=f"{player.name} ({player.persona.nickname})", description=f"General Stats of {player.name}", color=0x00ff00)

    embed.set_thumbnail(url=player.profile_pic_url_256)

    await player.load_ranked_v2()
    embed.add_field(name="Ranked Points", value=player.ranked_profile.rank_points, inline=False)
    embed.add_field(name="Rank", value=player.ranked_profile.rank, inline=False)
    embed.add_field(name="Max Rank Points (Season)", value=player.ranked_profile.max_rank_points, inline=False)
    embed.add_field(name="Max Rank (Season)", value=player.ranked_profile.max_rank, inline=False)

    await ctx.send(embed=embed)
    await auth.close()


@bot.hybrid_command()
async def gunstats(ctx: commands.Context, gunclass: Literal['AR', 'SMG', 'MP', 'LMG', 'DMR', 'SG', 'PISTOL', 'OTHER']):
    df = pd.read_csv('gunData.csv')
    filtered_df = df[df['Category'] == gunclass]
    filtered_df = filtered_df.sort_values(by='DPS')
    plt.figure(figsize=(10, 6))
    plt.bar(filtered_df['Name'], filtered_df['DPS'], color='skyblue')
    plt.xlabel('Gun Name')
    plt.ylabel('DPS')
    plt.title(f'Gun DPS for Category {gunclass}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('temp.png')
    file = discord.File('temp.png')
    await ctx.send(file=file)


#async def track_all_players():
    #for player in data["players"]:
        #await track(uid=player["ubiID"], discordIds=[reciever["discordID"] for reciever in data["recievers"] if reciever["user"] == player["name"]])


bot.run(os.getenv('DISCORD_TOKEN'))
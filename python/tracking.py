import asyncio
from siegeapi import Auth
import discord
import os
from dotenv import load_dotenv

load_dotenv(".env")

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
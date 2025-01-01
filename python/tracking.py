import asyncio
from siegeapi import Auth
import discord
import os
from dotenv import load_dotenv

load_dotenv("details/.env")

async def run():
    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    player = await auth.get_player(name="CNDRD")

    print(f"Name: {player.name}")
    print(f"Profile pic URL: {player.profile_pic_url}")

    await auth.close()
    
asyncio.get_event_loop().run_until_complete(run())
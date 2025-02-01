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
is_tracking = False


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)


with open("details/data.json", "r") as targets:
    data = json.load(targets)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')


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


async def track(uid: str, discordIds: list):
    global is_tracking
    while is_tracking:
        try:
            auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

            player = await auth.get_player(uid=uid)

            await player.load_ranked_v2()
            oldMMR = player.ranked_profile.rank_points
            oldKills = player.ranked_profile.kills
            oldDeaths = player.ranked_profile.deaths
            oldWins = player.ranked_profile.wins
            oldLosses = player.ranked_profile.losses

            await player.load_ranked_v2()
            newMMR = player.ranked_profile.rank_points
            newKills = player.ranked_profile.kills
            newDeaths = player.ranked_profile.deaths
            newWins = player.ranked_profile.wins
            newLosses = player.ranked_profile.losses

            if newMMR != oldMMR:
                mmrChange = newMMR - oldMMR

                winLossRatio = round(newWins / newLosses, 1)
                overallKD = round(newKills / newDeaths, 1)
                matchKills = newKills - oldKills
                matchDeaths = newDeaths - oldDeaths
                matchKD = round((newKills - oldKills) / (newDeaths - oldDeaths), 1)

                if mmrChange > 0:
                    mmrChange = f"+{mmrChange}"

                await player.load_persona()
    
                if not player.persona.enabled:
                    embed = discord.Embed(title=player.name, color=0x00ff00)
                else:
                    embed = discord.Embed(title=f"{player.name} ({player.persona.nickname})", color=0x00ff00)

                embed.add_field(name="Match Stats", value="", inline=False)
                embed.add_field(name="MMR Change", value=mmrChange, inline=False)
                embed.add_field(name="KD", value=f"{matchKills} - {matchDeaths} ({matchKD})", inline=False)

                embed.add_field(name="New Ranked Stats", value="", inline=False)
                embed.add_field(name="W/L Ratio", value=winLossRatio, inline=False)
                embed.add_field(name="Overall KD", value=overallKD, inline=False)

                for discordId in discordIds:
                    try:
                        user = await bot.fetch_user(discordId)
                        await user.send(embed=embed)
                        print(f'Sent DM to {discordId}')

                    except discord.HTTPException:
                        print(f'Failed to send DM to {discordId}')
                        continue
            
            else:
                print(f"No change in MMR detected for {player.name}")

            await auth.close()

            await asyncio.sleep(150)

        except RecursionError:
            print("Recursion Error")
            
            if is_tracking:
                continue

            continue

        except Exception as e:
            print(f"An error occurred: {e}")
            break


@bot.hybrid_command()
async def track_all_players(ctx):
    global is_tracking
    user_id = str(ctx.author.id)
    
    user_is_admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            user_is_admin = True
            break
    
    if not user_is_admin:
        await ctx.send("You do not have permission to use this command. Admin access required.")
        return

    if is_tracking:
        await ctx.send("Already tracking players. Use `/stop_tracking` to stop first.")
        return
        
    is_tracking = True
    await ctx.send("Started tracking all players.")
    
    for player in data["players"]:
        asyncio.create_task(track(uid=player["ubiID"], 
            discordIds=[reciever["discordID"] for reciever in data["recievers"] if reciever["user"] == player["name"]]))
        

@bot.hybrid_command()
async def stop_tracking(ctx):
    global is_tracking
    user_id = str(ctx.author.id)
    
    user_is_admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            user_is_admin = True
            break
    
    if not user_is_admin:
        await ctx.send("You do not have permission to use this command. Admin access required.")
        return

    if not is_tracking:
        await ctx.send("No tracking is currently active.")
        return
        
    is_tracking = False
    await ctx.send("Stopping all player tracking. This may take a few moments to complete.")


@bot.hybrid_command()
async def add_player(ctx, username: str):
    user_id = str(ctx.author.id)
    
    admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            admin = True
            break
    
    if not admin:
        await ctx.send("No permission.")
        return

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    player = await auth.get_player(username)
    ubiID = player.id
    
    for existing_player in data["players"]:
        if existing_player["ubiID"] == ubiID:
            await ctx.send(f"{username} is already being tracked.")
            await auth.close()
            return
    
    new_player = {
        "name": username,
        "ubiID": ubiID
    }
    
    data["players"].append(new_player)
    
    with open("details/data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await ctx.send(f"Successfully added {username} to tracking list.")
    await auth.close()


@bot.hybrid_command()
async def remove_player(ctx, username: str):
    user_id = str(ctx.author.id)
    
    admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            admin = True
            break
    
    if not admin:
        await ctx.send("No permission.")
        return

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    player_found = False
    for player in data["players"]:
        if player["name"].lower() == username.lower():
            data["players"].remove(player)
            player_found = True
            break
            
    if not player_found:
        await ctx.send(f"{username} is not being tracked.")
        await auth.close()
        return
        
    with open("details/data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await ctx.send(f"Successfully removed {username} from tracking list.")
    await auth.close()


bot.run(os.getenv('DISCORD_TOKEN'))
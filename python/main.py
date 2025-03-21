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


# Returns the general stats of a player
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


# Returns the ranked stats of a player
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


# Get the current gun stats for a specific category
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


# Used to track a player's stats
async def track(uid: str, discordIds: list):
    global is_tracking
    while is_tracking:
        try:
            auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))

            player = await auth.get_player(uid=uid)

            oldStats = None
            for player_data in data["players"]:
                if player_data["ubiID"] == uid:
                    oldStats = player_data
                    oldMMR = oldStats["rankPoints"]
                    oldKills = oldStats["kills"]  
                    oldDeaths = oldStats["deaths"]
                    oldWins = oldStats["wins"]
                    oldLosses = oldStats["losses"]
                    break

            await player.load_ranked_v2()
            newMMR = player.ranked_profile.rank_points
            newKills = player.ranked_profile.kills
            newDeaths = player.ranked_profile.deaths
            newWins = player.ranked_profile.wins
            newLosses = player.ranked_profile.losses

            # Check if there is a change in MMR
            if newMMR != oldMMR:
                mmrChange = newMMR - oldMMR

                winLossRatio = round(newWins / newLosses, 1)
                overallKD = round(newKills / newDeaths, 1)
                matchKills = newKills - oldKills
                matchDeaths = newDeaths - oldDeaths

                # Calculate KD
                if matchDeaths == 0:
                    matchKD = matchKills
                else:
                    matchKD = round((matchKills) / (matchDeaths), 1)

                if mmrChange > 0:
                    mmrChange = f"+{mmrChange}"

                await player.load_persona()
    
                if not player.persona.enabled:
                    embed = discord.Embed(title=player.name, color=0x00ff00)
                else:
                    embed = discord.Embed(title=f"{player.name} ({player.persona.nickname})", color=0x00ff00)

                embed.add_field(name="MMR Change", value=mmrChange, inline=False)
                embed.add_field(name="KD", value=f"{matchKills} - {matchDeaths} ({matchKD})", inline=False)

                embed.add_field(name="W/L Ratio", value=winLossRatio, inline=False)
                embed.add_field(name="Overall KD", value=overallKD, inline=False)
                embed.add_field(name="Rank" , value=player.ranked_profile.rank, inline=False)
                embed.add_field(name="Rank Points", value=newMMR, inline=False)

                # Send DM to all receivers
                for receiver in data["recievers"]:
                    try:
                        user = await bot.fetch_user(receiver["discordID"])
                        await user.send(embed=embed)
                        print(f'Sent DM to {receiver["user"]}')

                    # Handle exceptions
                    except discord.HTTPException:
                        print(f'Failed to send DM to {receiver["user"]}')
                        continue

                # Update player stats in data
                for player_data in data["players"]:
                    if player_data["ubiID"] == uid:
                        player_data["rankPoints"] = newMMR
                        player_data["kills"] = newKills
                        player_data["deaths"] = newDeaths 
                        player_data["wins"] = newWins
                        player_data["losses"] = newLosses
                        break

                # Save updated data to file
                with open("details/data.json", "w") as f:
                    json.dump(data, f, indent=4)
            
            else:
                print(f"No change in MMR detected for {player.name}")

            await auth.close()

            await asyncio.sleep(150)

        # Handle exceptions
        except RecursionError:
            print("Recursion Error")
            
            if is_tracking:
                continue

            continue

        # Handle exceptions
        except Exception as e:
            print(f"An error occurred: {e}")
            break


# Track a player
@bot.hybrid_command()
async def track_player(ctx, username: str):
    global is_tracking
    user_id = str(ctx.author.id)
    
    # Check if user is an admin
    user_is_admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            user_is_admin = True
            break
    
    if not user_is_admin:
        await ctx.send("You do not have permission to use this command. Admin access required.")
        return

    # Check if player exists in tracking list
    player_found = False
    player_uid = None
    for player in data["players"]:
        if player["name"].lower() == username.lower():
            player_found = True
            player_uid = player["ubiID"]
            break

    if not player_found:
        await ctx.send(f"Player {username} not found in tracking list. Add them first using `/add_player`.")
        return

    if is_tracking:
        await ctx.send("Already tracking players. Use `/stop_tracking` to stop first.")
        return
        
    is_tracking = True
    await ctx.send(f"Started tracking {username}.")
    
    # Get all receivers and start tracking
    discordIds = [receiver["discordID"] for receiver in data["recievers"]]
    asyncio.create_task(track(uid=player_uid, discordIds=discordIds))


# Track all players
@bot.hybrid_command()
async def track_all_players(ctx):
    global is_tracking
    user_id = str(ctx.author.id)
    
    # Check if user is an admin
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
    
    # Start tracking all players
    for player in data["players"]:
        asyncio.create_task(track(uid=player["ubiID"], 
            discordIds=[reciever["discordID"] for reciever in data["recievers"] if reciever["user"] == player["name"]]))


# Update all player stats
@bot.hybrid_command()
async def update_player_stats(ctx):
    user_id = str(ctx.author.id)
    
    # Check if user is an admin
    user_is_admin = False
    for receiver in data["recievers"]:
        if receiver["discordID"] == user_id and receiver["admin"]:
            user_is_admin = True
            break
    
    if not user_is_admin:
        await ctx.send("You do not have permission to use this command. Admin access required.")
        return

    auth = Auth(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    update_count = 0
    
    # Update each player's stats
    for player_data in data["players"]:
        try:
            player = await auth.get_player(uid=player_data["ubiID"])
            await player.load_ranked_v2()
            
            # Update player stats in data
            player_data["rankPoints"] = player.ranked_profile.rank_points
            player_data["kills"] = player.ranked_profile.kills
            player_data["deaths"] = player.ranked_profile.deaths
            player_data["wins"] = player.ranked_profile.wins
            player_data["losses"] = player.ranked_profile.losses
            
            update_count += 1
            
        except Exception as e:
            print(f"Error updating {player_data['name']}: {e}")
            continue

    # Save updated data to file
    with open("details/data.json", "w") as f:
        json.dump(data, f, indent=4)

    await ctx.send(f"Successfully updated stats for {update_count} players.")
    await auth.close()
        

# Stop tracking all players
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


# Add a player to the tracking list
@bot.hybrid_command()
async def add_player(ctx, username: str):
    user_id = str(ctx.author.id)
    
    # Check if user is an admin
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

    await player.load_ranked_v2()
    rankPoints = player.ranked_profile.rank_points
    rank = player.ranked_profile.rank
    kills = player.ranked_profile.kills
    deaths = player.ranked_profile.deaths
    wins = player.ranked_profile.wins
    losses = player.ranked_profile.losses
    
    ubiID = player.id
    
    # Check if player is already being tracked
    for existing_player in data["players"]:
        if existing_player["ubiID"] == ubiID:
            await ctx.send(f"{username} is already being tracked.")
            await auth.close()
            return
    
    # Add player to tracking list
    new_player = {
        "name": username,
        "ubiID": ubiID,
        "rankPoints": rankPoints,
        "kills": kills,
        "deaths": deaths,
        "wins": wins,
        "losses": losses
    }
    
    data["players"].append(new_player)
    
    # Save updated data to file
    with open("details/data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await ctx.send(f"Successfully added {username} to tracking list.")
    await auth.close()


# Remove a player from the tracking list
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
        
    # Save updated data to file
    with open("details/data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await ctx.send(f"Successfully removed {username} from tracking list.")
    await auth.close()


bot.run(os.getenv('DISCORD_TOKEN'))
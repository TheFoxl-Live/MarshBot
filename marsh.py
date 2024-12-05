import discord
import ezcord
import os
from discord.ext import commands, bridge
from dotenv import load_dotenv

load_dotenv()

bot = ezcord.BridgeBot(
    intents=discord.Intents.all(),
    language="de",
    command_prefix="!",
)

@bot.event
async def on_ready():
    print(f'Eingeloggt als {bot.user}')
    await bot.change_presence(activity=discord.Streaming(name="Marshmallows am Lagerfeuer!", url=f"https://twitch.tv/nikonici1990"))

if __name__ == "__main__":
    bot.load_cogs("cogs")
    bot.run(os.getenv('DISCORD_TOKEN'))

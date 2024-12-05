import discord
from discord.ext import commands, tasks
import re

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_empty_channels.start()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        original_channel_name = "🔥𝗟𝗮𝗴𝗲𝗿𝗳𝗲𝘂𝗲𝗿"
        original_channel = discord.utils.get(member.guild.voice_channels, name=original_channel_name)

        if after.channel and (after.channel == original_channel or after.channel.name.startswith("🔥𝗟𝗮𝗴𝗲𝗿𝗳𝗲𝘂𝗲𝗿")):
            existing_channels = [
                vc for vc in member.guild.voice_channels 
                if vc.name.startswith("🔥𝗟𝗮𝗴𝗲𝗿𝗳𝗲𝘂𝗲𝗿") and vc != original_channel
            ]

            if existing_channels:
                max_number = max(
                    int(re.search(r'\d+$', vc.name).group()) for vc in existing_channels
                )
            else:
                max_number = 1

            if all(len(channel.members) > 0 for channel in [original_channel] + existing_channels):
                next_number = max_number + 1
                new_channel = await member.guild.create_voice_channel(
                    f"🔥𝗟𝗮𝗴𝗲𝗿𝗳𝗲𝘂𝗲𝗿 {next_number}",
                    bitrate=original_channel.bitrate,
                    user_limit=original_channel.user_limit,
                    overwrites=original_channel.overwrites,
                    category=original_channel.category
                )
                print(f"Neuer Channel erstellt: {new_channel.name}")

    @tasks.loop(seconds=30)
    async def check_empty_channels(self):
        guild = self.bot.guilds[0]
        original_channel_name = "🔥𝗟𝗮𝗴𝗲𝗿𝗳𝗲𝘂𝗲𝗿"

        original_channel = discord.utils.get(guild.voice_channels, name=original_channel_name)
        if original_channel is None:
            return

        if len(original_channel.members) == 0:
            channels_to_delete = [
                vc for vc in guild.voice_channels 
                if vc.name.startswith(original_channel_name) and vc.name != original_channel_name
            ]
            for channel in channels_to_delete:
                if len(channel.members) == 0:
                    await channel.delete()
                    print(f"Leerer Channel gelöscht: {channel.name}")
        else:
            channels_to_check = [
                vc for vc in guild.voice_channels 
                if vc.name.startswith(original_channel_name) and vc.name != original_channel_name
            ]
            channels_to_check.sort(key=lambda vc: int(re.search(r'\d+$', vc.name).group()), reverse=True)

            for channel in channels_to_check:
                if len(channel.members) == 0 and channel.name != f"{original_channel_name} 2":
                    await channel.delete()
                    print(f"Leerer Channel gelöscht: {channel.name}")
                    break

    @check_empty_channels.before_loop
    async def before_check_empty_channels(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Voice(bot))
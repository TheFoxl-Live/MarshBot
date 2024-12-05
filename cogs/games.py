import asyncio

import discord
from discord.ext import commands

class GameRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1255571805742043176
        self.message_id = 1296929500650672213
        self.image_url = "https://nextcloud.universe-of-gaming.de/s/YRPipDXErjTRtgp/preview"
        self.reactions_roles = {
            '🐪': 1255770708320059453,
            '🪓': 1255770629882511433,  
            '🌼': 1250313657859178606,  
            '👻': 1255770256845312011,  
            '🐑': 1255770208648433665,  
            '🐭': 1255770563356659732,  
            '🦖': 1255770152226652231,  
            '🎱': 1255770474206466108,  
            '⛺': 1294590405517508680,  
            '🌸': 1294032703431376907,  
            '🌲': 1296925048883646536             
        }

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        channel = self.bot.get_channel(self.channel_id)
        if self.message_id is None:
            x = '‎'
            await channel.send(self.image_url)
            embed = discord.Embed(title="🎮 1. Welche Games spielst du?",
                                  description=f"Welche der folgenden Games spielst du?\nWähle den dazugehörigen Emoji, um den Zugriff mit der bestimmten Rolle zu erhalten!",
                                  colour=discord.Color.from_rgb(32, 153, 0))

            embed.set_author(name="× Rollenvergabe",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

            embed.add_field(name="__Verfügbare Rollen__",
                            value="🐪 » <@&1255770708320059453>\n🪓 » <@&1255770629882511433>\n🌼 » <@&1250313657859178606>\n👻 » <@&1255770256845312011>\n🐑 » <@&1255770208648433665>\n🐭 » <@&1255770563356659732>\n🦖 » <@&1255770152226652231>\n🎱 » <@&1255770474206466108>\n⛺ » <@&1294590405517508680>\n🌸 » <@&1294032703431376907>\n🌲 » <@&1296925048883646536>",
                            inline=False)

            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")


            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

            message = await channel.send(embed=embed)
            await channel.send(f"{x}\n{x}")
            self.message_id = message.id
            for emoji in self.reactions_roles.keys():
                await message.add_reaction(emoji)
        else:
            message = await channel.fetch_message(self.message_id)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        emoji = str(payload.emoji)
        role_id = self.reactions_roles.get(emoji)
        if role_id:
            role = guild.get_role(role_id)
            if role:
                member = guild.get_member(payload.user_id)
                if member and member != self.bot.user:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        emoji = str(payload.emoji)
        role_id = self.reactions_roles.get(emoji)
        if role_id:
            role = guild.get_role(role_id)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(role)

def setup(bot):
    bot.add_cog(GameRoles(bot))

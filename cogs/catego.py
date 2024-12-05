import asyncio
import discord
from discord.ext import commands

class ChannelRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1255571805742043176
        self.message_id = 1296929521710403624
        self.image_url = "https://nextcloud.universe-of-gaming.de/s/jHrNRJGkicfzEKg/preview"
        self.reactions_roles = {
            '🥵': 1294033733225152565
        }

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(10)
        channel = self.bot.get_channel(self.channel_id)
        if self.message_id is None:
            x = '‎'
            await channel.send(self.image_url)
            embed = discord.Embed(title="🖥 2. Welche Kanäle möchtest du sehen?",
                                  description=f"Welche der folgenden Kanäle möchtest du sehen?\nWähle den dazugehörigen Emoji, um den Zugriff mit der bestimmten Rolle zu erhalten!",
                                  colour=discord.Color.from_rgb(32, 153, 0))

            embed.set_author(name="× Rollenvergabe",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

            embed.add_field(name="__Verfügbare Rollen__",
                            value="🥵 » <@&1294033733225152565>",
                            inline=False)

            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")


            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

            message = await channel.send(embed=embed)
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
    bot.add_cog(ChannelRoles(bot))
 
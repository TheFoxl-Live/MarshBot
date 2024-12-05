import discord
from discord.ext import commands, bridge
from discord.ext.commands import BadArgument


class Hack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command(name="hack", description="Umarme eine @Person", guild_ids=[411540009846571009])
    async def hack(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        await ctx.respond(content=f"{ctx.author.mention} umarmt {member.mention} ganz dolle 🤗. Aber pass auf, nicht zu fest, sonst gibt's Hack... 😅")

    @hack.error
    async def hack_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, leider kann ich dieses Mitglied nicht auf dem Server finden.")

            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)



    @bridge.bridge_command(name="rehhack", description="Umarme eine @Person zurück", guild_ids=[411540009846571009])
    async def rehhack(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        await ctx.respond(content=f"{ctx.author.mention} umarmt auch {member.mention} und Plopp, schon haben wir Hack! 😂")

    @rehhack.error
    async def rehhack_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, leider kann ich dieses Mitglied nicht auf dem Server finden.")

            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Hack(bot))


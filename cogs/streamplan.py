from discord import slash_command
from discord.ext import commands

class Streamplan(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="streamplan", description="Setzt den Streamplan", guild_ids=[411540009846571009])
    @commands.has_role(1294602830807830639)
    async def splan_command(self, ctx, message: str):
        
        await ctx.respond("Der Streamplan wurde gesendet!", ephemeral=True)
        channel = self.bot.get_channel(1294364244392808459)
        await channel.send(content=f"<@&1102982788497559632>\n{message}")

        return

def setup(bot):
    bot.add_cog(Streamplan(bot))

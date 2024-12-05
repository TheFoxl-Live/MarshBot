import discord
from discord import option, slash_command
from discord.ext import commands

class Verify(commands.Cog):
    def __init__(self, bot, role_ids):
        self.bot = bot
        self.role_ids = role_ids

    @slash_command(name="createverify", description="Hinterlegt den Verifizierungschannel",
                guild_ids=[411540009846571009])
    @option(
        "Channel",
        str,
        description="Bitte nenne den Channel, den du hinterlegen möchtest:"
    )
    async def create_verify(self, ctx, channel: discord.TextChannel):
        perm = discord.utils.get(ctx.guild.roles, id=414963308030853120)
        if perm in ctx.author.roles:
            embed = discord.Embed(
                description=(
                    f"Hier gelten die Discord und Twitch Regeln! \n"
                    f"Um dich zu Verifizieren, drücke unten auf den Button!"
                ),
                color=discord.Color.from_rgb(255, 0, 255)
            )
            embed.set_author(name="» Verifizieren", icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.add_field(
                name="**Wichtig!**",
                value="**Mit dem Drücken des Buttons akzeptierst du automatisch das Regelwerk!**"
            )
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!", icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

            view = discord.ui.View(timeout=None)
            button = discord.ui.Button(label="Klick mich hart!!", emoji="<:ShockedOctoEmote112:1036204422541352990>", style=discord.ButtonStyle.danger, custom_id="MarshVerify")
            view.add_item(button)

            try:
                await channel.send(embed=embed, view=view)
                await ctx.respond("Der Verify-Channel wurde erfolgreich gesetzt!", ephemeral=True)
            except Exception as e:
                await ctx.respond("Es ist ein Fehler aufgetreten! Bitte kontaktiere die Administration!", ephemeral=True)
        else:
            await ctx.respond("Du hast nicht die erforderliche Berechtigung, diesen Befehl auszuführen.")

class VerifyInteraction(commands.Cog):
    def __init__(self, bot, role_ids):
        self.bot = bot
        self.role_ids = role_ids

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        global role
        if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == 'MarshVerify':
            member = await self.bot.guilds[0].fetch_member(interaction.user.id)
            role_ids = [1102982788497559632, 1294036704528699432]

            for id in role_ids:
                role = member.guild.get_role(id)

            if role in member.roles:
                await interaction.response.send_message('**Du bist bereits verifiziert!**', ephemeral=True)
            else:
                await interaction.response.send_message('**Du wurdest erfolgreich verifiziert! Viel Spaß auf dem Discord!**', ephemeral=True)
                await member.add_roles(*[discord.Object(role_id) for role_id in role_ids])


def setup(bot):
    role_ids = {
        'verified': [1102982788497559632, 1294036704528699432]
    }
    bot.add_cog(Verify(bot, role_ids))
    bot.add_cog(VerifyInteraction(bot, role_ids))

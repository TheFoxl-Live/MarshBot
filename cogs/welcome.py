import discord
from discord.ext import commands
from easy_pil import Editor, Font, load_image_async
class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        background = Editor("img/utils/wel.png").resize((900, 270)).rounded_corners((30))
        profile_image = await load_image_async(member.display_avatar.url)
        profile = Editor(profile_image).resize((200, 200)).circle_image()
        
        border_thickness = 10
        background.rectangle(
            (0, 0),
            width=910 - border_thickness,
            height=280 - border_thickness,
            outline="#ffffff",
            stroke_width=border_thickness,
            radius=30
        )

        poppins_big = Font.poppins(variant="bold", size=50)
        poppins_mediam = Font.poppins(variant="bold", size=40)
        poppins_regular = Font.poppins(variant="regular", size=35)
        poppins_thin = Font.poppins(variant="bold", size=25)

        background.paste(profile, (40, 35))
        background.ellipse((40, 35), 200, 200, outline="white", stroke_width=3)
        background.text((600, 50), "WILLKOMMEN", font=poppins_big, color="white", align="center")
        background.text(
            (600, 100), f"{member.display_name}", font=poppins_regular, color="gold", align="center"
        )
        background.text(
            (600, 160), "MITGLIED", font=poppins_mediam, color="white", align="center"
        )
        background.text(
            (600, 200), f"#{len(member.guild.members)}", font=poppins_regular, color="gold", align="center"
        )

        channel = self.bot.get_channel(1304849833202290832)
        file = discord.File(fp=background.image_bytes, filename="welcome.png")
        await channel.send(content=f":wave: Hallöchen {member.mention}, willkommen bei der :dango: Marshmallow Bande – mach’s dir gemütlich und viel Spaß! :video_game::fire:", file=file)

        
def setup(bot):
    bot.add_cog(Welcome(bot))


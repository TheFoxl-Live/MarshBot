import discord
import aiosqlite
from discord.ext import commands, bridge
from discord.ext.commands import BadArgument
from easy_pil import Editor, Font, load_image_async
import random
import time

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = "marsh.db"
        self.last_xp_time = {}

    @staticmethod
    def get_level(xp):
        lvl = 1
        amount = 100
        while True:
            xp -= amount
            if xp < 0:
                return lvl
            lvl += 1
            amount += 100

    @staticmethod
    def xp_for_level(level):
        total_xp = 0
        for lvl in range(1, level):
            total_xp += 100 + (lvl - 1) * 100
        return total_xp

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                msg_count INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0
                )
                """
            )

    async def check_user(self, user_id):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def get_xp(self, user_id):
        await self.check_user(user_id)
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT xp FROM users WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
        return result[0] if result else 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        current_time = time.time()
        user_id = message.author.id

        if user_id in self.last_xp_time and current_time - self.last_xp_time[user_id] < 60:
            return

        xp = random.randint(10, 25)

        await self.check_user(message.author.id)
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                "UPDATE users SET msg_count = msg_count + 1, xp = xp + ? WHERE user_id = ?", (xp, message.author.id)
            )
            await db.commit()

        self.last_xp_time[user_id] = current_time
        new_xp = await self.get_xp(message.author.id)
        old_level = self.get_level(new_xp - xp)
        new_level = self.get_level(new_xp)

        if old_level != new_level:
            channel = self.bot.get_channel(1304778502259609702)
            await channel.send(f"🍬 Woohoo, {message.author.mention}! 🍬\nDu bist jetzt **Level {new_level}** und ein noch süßerer Marshmallow! 🔥🥇")

    @bridge.bridge_command(name="rank", description="Sieh dir deinen Rank auf dem Server an", guild_ids=[411540009846571009])
    @bridge.bridge_option("user", discord.Member, description="Der Nutzer, dessen Geburtstag angezeigt werden soll.", required=False)
    async def rank(self, ctx, user = None):
        
        if user is None:
            user = ctx.author

        user_id = str(user.id)
        
        xp = await self.get_xp(user_id)
        lvl = self.get_level(xp)

        current_level_xp = self.xp_for_level(lvl)
        next_level_xp = self.xp_for_level(lvl + 1)
        xp_needed = next_level_xp - current_level_xp
        xp_progress = xp - current_level_xp

        progress_percen = xp_progress / xp_needed
        progress_percent = progress_percen * 100

        background = Editor("img/utils/level.png").resize((934, 282)).rounded_corners((30))
        profile_image = await load_image_async(user.display_avatar.url)
        profile = Editor(profile_image).resize((190, 190)).circle_image()

        poppins = Font.poppins(size=30)

        border_thickness = 10
        background.rectangle(
            (0, 0),
            width=940 - border_thickness,
            height=289 - border_thickness,
            outline="#ffffff",
            stroke_width=border_thickness,
            radius=30
        )

        background.paste(profile, (50, 50))
        background.ellipse((42, 42), width=206, height=206, outline="#43b581", stroke_width=10)
        background.rectangle((260, 180), width=630, height=40, fill="#484b4e", radius=20)
        background.bar(
            (260, 180),
            max_width=630,
            height=40,
            percentage=progress_percent,
            fill="#00fa81",
            radius=20,
        )
        background.text((270, 120), user.display_name, font=poppins, color="#00fa81")
        background.text(
            (870, 125),
            f"{xp_progress} / {xp_needed} XP",
            font=poppins,
            color="#00fa81",
            align="right",
        )


        background.text((770, 30), "Level", font=poppins, color="#00fa81")
        background.text((850, 30), f"{lvl}", font=poppins, color="#1EAAFF")

        # Bild senden
        file = discord.File(fp=background.image_bytes, filename="rank.png")
        await ctx.respond(file=file)

    @rank.error
    async def rank_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, leider kann ich dieses Mitglied nicht auf dem Server finden.")

            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                                icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
        
    @bridge.bridge_command(name="leaderboard", description="Sieh dir das Leaderboard auf dem Server an", guild_ids=[411540009846571009])
    async def leaderboard(self, ctx):
        leaderboard_data = []
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute(
                    "SELECT user_id, xp FROM users WHERE msg_count > 0 ORDER BY xp DESC LIMIT 5"
            ) as cursor:
                async for user_id, xp in cursor:
                    leaderboard_data.append((user_id, xp))

        background_image = Editor("img/utils/LB.png")

        entry_font = Font.poppins(size=20)

        y_position = 20
        for i, (user_id, xp) in enumerate(leaderboard_data, start=1):
            user = self.bot.get_user(user_id).name
            lvl = self.get_level(xp)
            user_tag = f"{user}"
            lvl_text = f"Level {lvl}"
            xp_text = f"{xp} XP"
            background_image.text((70, y_position), user_tag, font=entry_font, color="white")
            background_image.text((360, y_position), lvl_text, font=entry_font, color="yellow")
            background_image.text((470, y_position), xp_text, font=entry_font, color="yellow")
            y_position += 85

        leaderboard_image = background_image.image_bytes
        file = discord.File(leaderboard_image, filename="leaderboard.png")

        await ctx.respond(file=file, content="Hier ist das aktuelle Leaderboard:")
        
        
def setup(bot):
    bot.add_cog(LevelSystem(bot))

import datetime
import discord
from discord.ext import commands, tasks, bridge
from datetime import timedelta
import aiosqlite
from discord.ext.commands import BadArgument, MissingRequiredArgument


class Bday(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.loop = self.bot.loop
        self.loop.run_until_complete(self.init_db())
        self.birthday_reminder.start()

    async def init_db(self):
        async with aiosqlite.connect("marsh.db") as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS birthdays (
                user_id TEXT PRIMARY KEY,
                birthday TEXT NOT NULL
            )
            ''')
            await db.commit()

    async def load_birthdays(self):
        birthdays = {}
        async with aiosqlite.connect("marsh.db") as db:
            async with db.execute('SELECT user_id, birthday FROM birthdays') as cursor:
                async for row in cursor:
                    birthdays[row[0]] = row[1]
        return birthdays

    async def save_birthday(self, user_id, birthday):
        async with aiosqlite.connect("marsh.db") as db:
            await db.execute('INSERT OR REPLACE INTO birthdays (user_id, birthday) VALUES (?, ?)', (user_id, birthday))
            await db.commit()

    async def forget_birthday(self, user_id):
        async with aiosqlite.connect("marsh.db") as db:
            await db.execute('DELETE FROM birthdays WHERE user_id = ?', (user_id,))
            await db.commit()

    @tasks.loop(hours=24)
    async def birthday_reminder(self):
        self.birthdays = await self.load_birthdays()
        now = datetime.datetime.now()
        today = now.strftime("%d-%m")
        channel = self.bot.get_channel(1102994912774996029)
        for user_id, date in self.birthdays.items():
            parts = date.split('-')
            if len(parts) == 3:
                day, month, year = parts
                birth_date = datetime.datetime(year=int(year), month=int(month), day=int(day))
                age = now.year - birth_date.year - ((now.month, now.day) < (birth_date.month, birth_date.day))
            else:
                day, month = parts
                age = None

            if f"{day}-{month}" == today:
                user = self.bot.get_user(int(user_id))
                if user:
                    if age is not None:
                        await channel.send(f"🎂 Heute wird {user.mention} **{age}** Jahre.\nLasst uns anstoßen mit einer Wolke aus Marshmallows und auf viele weitere süße Jahre! 🍡🥳")
                    else:
                        await channel.send(f"🎂 Heute wird {user.mention} ein Jahr älter.\nLasst uns anstoßen mit einer Wolke aus Marshmallows und auf viele weitere süße Jahre! 🍡🥳")

    @birthday_reminder.before_loop
    async def before_birthday_reminder(self):
        await discord.utils.sleep_until(datetime.datetime.combine(datetime.datetime.now() + timedelta(days=1), datetime.datetime.min.time()))
    
    @bridge.bridge_command(name="remember-birthday", description="Ich erinnere dich an deinem Geburtstag hier im Chat!",
                    guild_ids=[411540009846571009])
    @bridge.bridge_option("date", str, description="Das Geburtstagsdatum (TT-MM oder TT-MM-JJJJ).", required=True)
    async def rememberbirthday_command(self, ctx, date):
        user_id = str(ctx.author.id)
        self.birthdays = await self.load_birthdays()

        async def send_error_message():
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=(
                    "🚫 Das eingegebene Datum scheint nicht im richtigen Format zu sein. "
                    "\n\n**Verwendung:**\n"
                    "- </remember-birthday:1297266613954805860> `26-06`\n"
                    "- </remember-birthday:1297266613954805860> `26-06-1998`\n"
                    "\n"
                    "- **!remember-birthday** `26-06`\n"
                    "- **!remember-birthday** `26-06-1998`\n"
                )
            )
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

        if user_id in self.birthdays:
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, du hast bereits deinen Geburtstag hinterlegt: **{self.birthdays[user_id]}**.")
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
            return

        parts = date.split('-')
        if len(parts) not in [2, 3] or not all(part.isdigit() for part in parts):
            await send_error_message()
            return

        try:
            if len(parts) == 3:
                day, month, year = map(int, parts)
                if not (1 <= month <= 12) or not (1 <= day <= 31) or not (1900 <= year <= 2100):
                    await send_error_message()
                    return
                birth_date = datetime.datetime(year=year, month=month, day=day)
            elif len(parts) == 2:
                day, month = map(int, parts)
                if not (1 <= month <= 12) or not (1 <= day <= 31):
                    await send_error_message()
                    return
                now = datetime.datetime.now()
                birth_date = datetime.datetime(now.year, month, day)

        except ValueError:
            await send_error_message()
            return

        self.birthdays[user_id] = date
        await self.save_birthday(user_id, date)
        now = datetime.datetime.now()

        if len(parts) == 3:
            day, month, year = parts
            birth_date = datetime.datetime(year=int(year), month=int(month), day=int(day))
            age = now.year - birth_date.year - ((now.month, now.day) < (birth_date.month, birth_date.day))
            next_birthday = datetime.datetime(now.year, int(month), int(day))

            if next_birthday < now:
                next_birthday = datetime.datetime(now.year + 1, int(month), int(day))
            days_until_birthday = (next_birthday - now).days
            date_discord = f"<t:{int(next_birthday.timestamp())}:D>"
            embed = discord.Embed(
                colour=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                description=f"📝 Ich habe es aufgeschrieben:\nIn **{days_until_birthday}** Tagen, am **{date_discord}**, wird {ctx.author.mention} **{age}** Jahre!\n\nDas wird eine süße Feier – mit jeder Menge Marshmallows, um das Alter zu feiern! 🍬🎂")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
        elif len(parts) == 2:
            day, month = parts
            next_birthday = datetime.datetime(now.year, int(month), int(day))

            if next_birthday < now:
                next_birthday = datetime.datetime(now.year + 1, int(month), int(day))
            days_until_birthday = (next_birthday - now).days
            date_discord = f"<t:{int(next_birthday.timestamp())}:D>"
            embed = discord.Embed(
                colour=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                description=f"📝 Ich habe es aufgeschrieben: Am **{date_discord}**, wird {ctx.author.mention} ein Jahr älter!\n\nDas wird eine süße Feier – mit jeder Menge Marshmallows, um das Alter zu feiern! 🍬🎂")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

    @rememberbirthday_command.error
    async def rememberbirthday_command_error(self, ctx, exc):
        async def send_error_message():
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=(
                    "🚫 Das eingegebene Datum scheint nicht im richtigen Format zu sein. "
                    "\n\n**Verwendung:**\n"
                    "- </remember-birthday:1297266613954805860> `26-06`\n"
                    "- </remember-birthday:1297266613954805860> `26-06-1998`\n"
                    "\n"
                    "- **!remember-birthday** `26-06`\n"
                    "- **!remember-birthday** `26-06-1998`\n"
                )
            )
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
        if isinstance(exc, MissingRequiredArgument):
            await send_error_message()
        elif isinstance(exc, BadArgument):
            await  send_error_message()

    
    @bridge.bridge_command(name="forget-birthday", description="Vergesse deinen Geburtstag hier im Chat!", 
                    guild_ids=[411540009846571009])
    async def forgetbirthday_command(self, ctx):
        user_id = str(ctx.author.id)
        self.birthdays = await self.load_birthdays()

        if user_id not in self.birthdays:
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, du hast noch keinen Geburtstag hinterlegt, den ich vergessen könnte.")
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
            return

        await self.forget_birthday(user_id)

        embed = discord.Embed(
            colour=discord.Color.blue(),
            description=f"🗑️ {ctx.author.mention}, ich habe deinen Geburtstag erfolgreich vergessen.")
        embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                         icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        embed.set_author(name="» Geburtstag",
                         icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        embed.set_thumbnail(url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

        await ctx.respond(embed=embed)

    
    @bridge.bridge_command(name="birthday", description="Zeigt den Geburtstag eines Nutzers an oder deinen eigenen.", 
                    guild_ids=[411540009846571009])
    @bridge.bridge_option("user", discord.Member, description="Der Nutzer, dessen Geburtstag angezeigt werden soll.")
    async def birthday(self, ctx, user: discord.Member = None):
        self.birthdays = await self.load_birthdays()
        if user is None:
            user = ctx.author

        user_id = str(user.id)
        if user_id in self.birthdays:
            date = self.birthdays[user_id]
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🎉 {user.mention}'s Geburtstag ist am **{date}**.")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
        else:
            if user == ctx.author:
                embed = discord.Embed(
                    colour=discord.Color.blue(),
                    description=f"🚫 {user.mention}, ich kenne deinen Geburtstag leider noch nicht.\n\nNutze </remember-birthday:1297266613954805860>, um deinen Geburtstag festzulegen!")
            else:
                embed = discord.Embed(
                    colour=discord.Color.blue(),
                    description=f"🚫 {ctx.author.mention}, ich kenne den Geburtstag von {user.mention} leider noch nicht.\n\nBitte {user.mention}, seinen Geburtstag mit </remember-birthday:1297266613954805860> zu hinterlegen!")
            
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")    
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

    @birthday.error
    async def birthday_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=f"🚫 {ctx.author.mention}, leider kann ich dieses Mitglied nicht auf dem Server finden.")

            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)
    
    @bridge.bridge_command(name="set-user-birthday", description="Admin-Befehl, um den Geburtstag eines Nutzers festzulegen.", 
                    guild_ids=[411540009846571009])
    @bridge.has_permissions(administrator=True)
    @bridge.bridge_option("user", discord.Member, description="Der Nutzer, dessen Geburtstag festgelegt wird", required=True)
    @bridge.bridge_option("date", str, description="Das Geburtstagsdatum (TT-MM oder TT-MM-JJJJ).", required=True)
    async def set_user_birthday(self, ctx, user, date):
        async def send_error_message():
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=(
                    "🚫 Die Eingabe scheint nicht im richtigen Format zu sein. "
                    "\n\n**Verwendung:**\n"
                    f"- </set-user-birthday:1297266613954805863> {ctx.author.mention} `26-06`\n"
                    f"- </set-user-birthday:1297266613954805863> {ctx.author.mention} `26-06-1998`\n"
                    "\n"
                    f"- **!set-user-birthday** {ctx.author.mention} `26-06`\n"
                    f"- **!set-user-birthday** {ctx.author.mention} `26-06-1998`\n"
                )
            )
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                             icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

        parts = date.split('-')
        if len(parts) not in [2, 3] or not all(part.isdigit() for part in parts):
            await send_error_message()
            return

        try:
            if len(parts) == 3:
                day, month, year = map(int, parts)
                if not (1 <= month <= 12) or not (1 <= day <= 31) or not (1900 <= year <= 2100):
                    await send_error_message()
                    return
                birth_date = datetime.datetime(year=year, month=month, day=day)
            elif len(parts) == 2:
                day, month = map(int, parts)
                if not (1 <= month <= 12) or not (1 <= day <= 31):
                    await send_error_message()
                    return
                now = datetime.datetime.now()
                birth_date = datetime.datetime(now.year, month, day)

        except ValueError:
            await send_error_message()
            return
      
        user_id = str(user.id)
        self.birthdays = await self.load_birthdays()
        self.birthdays[user_id] = date
        await self.save_birthday(user_id, date)

        embed = discord.Embed(
              colour=discord.Color.blue(),
              description=f"📅 Der Geburtstag von {user.mention} wurde auf **{date}** gesetzt.")
        embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                           icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        embed.set_author(name="» Geburtstag",
                           icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")

        await ctx.respond(embed=embed)

    @set_user_birthday.error
    async def set_user_birthday_error(self, ctx, exc):
        async def send_error_message():
            embed = discord.Embed(
                colour=discord.Color.blue(),
                description=(
                    "🚫 Die Eingabe scheint nicht im richtigen Format zu sein. "
                    "\n\n**Verwendung:**\n"
                    f"- </set-user-birthday:1297266613954805863> {ctx.author.mention} `26-06`\n"
                    f"- </set-user-birthday:1297266613954805863> {ctx.author.mention} `26-06-1998`\n"
                    "\n"
                    f"- **!set-user-birthday** {ctx.author.mention} `26-06`\n"
                    f"- **!set-user-birthday** {ctx.author.mention} `26-06-1998`\n"
                )
            )
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                            icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            embed.set_author(name="» Geburtstag",
                            icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
            await ctx.respond(embed=embed)

        if isinstance(exc, MissingRequiredArgument):
            await send_error_message()
        elif isinstance(exc, BadArgument):
            await  send_error_message()

def setup(bot):
    bot.add_cog(Bday(bot))

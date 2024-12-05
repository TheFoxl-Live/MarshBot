import datetime
import discord
import aiohttp
import aiosqlite
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks, bridge

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()

        self.TWITCH_CLIENT_ID = os.getenv('CLIENT_ID')
        self.TWITCH_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        self.twitch_access_token = None
        self.token_expiry = None

        self.streamers_live_status = {}
        self.stream_messages = {}
        self.watchlist = []

        self.bot.loop.create_task(self.init_db())
        self.check_streamers.start()

    async def init_db(self):
        async with aiosqlite.connect('marsh.db') as db:
            await db.executescript('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    streamer_name TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS streamers_status (
                    streamer_name TEXT PRIMARY KEY,
                    is_live INTEGER
                );
                CREATE TABLE IF NOT EXISTS stream_messages (
                    streamer_name TEXT PRIMARY KEY,
                    message_id INTEGER
                );
            ''')
            await db.commit()

        self.watchlist = await self.load_watchlist()
        self.streamers_live_status = await self.load_streamers_status()
        self.stream_messages = await self.load_stream_messages()

    async def load_watchlist(self):
        async with aiosqlite.connect('marsh.db') as db:
            async with db.execute('SELECT streamer_name FROM watchlist') as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def add_to_watchlist(self, streamer_name):
        async with aiosqlite.connect('marsh.db') as db:
            await db.execute('INSERT OR IGNORE INTO watchlist (streamer_name) VALUES (?)', (streamer_name,))
            await db.commit()

    async def remove_from_watchlist(self, streamer_name):
        async with aiosqlite.connect('marsh.db') as db:
            await db.execute('DELETE FROM watchlist WHERE streamer_name = ?', (streamer_name,))
            await db.commit()

    async def load_streamers_status(self):
        async with aiosqlite.connect('marsh.db') as db:
            async with db.execute('SELECT streamer_name, is_live FROM streamers_status') as cursor:
                return {row[0]: bool(row[1]) for row in await cursor.fetchall()}

    async def save_streamer_status(self, streamer_name, is_live):
        async with aiosqlite.connect('marsh.db') as db:
            await db.execute('INSERT OR REPLACE INTO streamers_status (streamer_name, is_live) VALUES (?, ?)', (streamer_name, int(is_live)))
            await db.commit()

    async def load_stream_messages(self):
        async with aiosqlite.connect('marsh.db') as db:
            async with db.execute('SELECT streamer_name, message_id FROM stream_messages') as cursor:
                return {row[0]: row[1] for row in await cursor.fetchall()}

    async def save_stream_message(self, streamer_name, message_id):
        async with aiosqlite.connect('marsh.db') as db:
            await db.execute('INSERT OR REPLACE INTO stream_messages (streamer_name, message_id) VALUES (?, ?)', (streamer_name, message_id))
            await db.commit()

    async def delete_stream_message(self, streamer_name):
        async with aiosqlite.connect('marsh.db') as db:
            await db.execute('DELETE FROM stream_messages WHERE streamer_name = ?', (streamer_name,))
            await db.commit()

    async def save_to_db(self, table, data):
        async with aiosqlite.connect('marsh.db') as db:
            async with db.cursor() as cursor:
                for query, params in data:
                    await cursor.execute(query, params)
            await db.commit()

    async def get_twitch_access_token(self, client_id, client_secret):
        url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
                return data['access_token']


    async def get_stream_data(self, access_token, client_id, streamer_name):
        url = f'https://api.twitch.tv/helix/streams?user_login={streamer_name}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json(content_type=None)
                return data['data'][0] if data['data'] else None

    async def get_user_data(self, access_token, client_id, streamer_name):
        url = f'https://api.twitch.tv/helix/users?login={streamer_name}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json(content_type=None)
                return data['data'][0] if data['data'] else None
                                
    async def download_image(self, url, save_path):
        if os.path.exists(save_path):
            os.remove(save_path)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        with open(save_path, 'wb') as file:
                            file.write(data)
                    else:
                        return
        except Exception as e:
            print(f"Fehler beim Herunterladen des Thumbnails: {e}")

    @tasks.loop(seconds=30)
    async def check_streamers(self): 
        await self.bot.wait_until_ready()
        try:
            access_token = await self.get_twitch_access_token(self.TWITCH_CLIENT_ID, self.TWITCH_CLIENT_SECRET)
            watchlist = await self.load_watchlist()

            current_live_status = await self.load_streamers_status()
            
            self.stream_messages = await self.load_stream_messages()

            for streamer in watchlist:
                stream_data = await self.get_stream_data(access_token, self.TWITCH_CLIENT_ID, streamer)
                is_live = stream_data is not None

                if is_live and not current_live_status.get(streamer, False):
                    user_data = await self.get_user_data(access_token, self.TWITCH_CLIENT_ID, streamer)
                    if user_data:
                        channel = self.get_channel_for_streamer(streamer)
                        embed, file = await self.create_embed(stream_data, user_data)
                        message_content = f"Der/die fantastische **{user_data['display_name']}** spielt gerade **{stream_data['game_name']}**.\nSchau doch mal vorbei, setz dich mit ans Lagerfeuer und genieß die Marshmallows!"

                        message = await channel.send(message_content, embed=embed, file=file)

                        await self.save_stream_message(streamer, message.id)
                        await self.save_streamer_status(streamer, True)

                elif not is_live and current_live_status.get(streamer, True):
                    # Lösche Nachricht, wenn der Streamer offline ist
                    message_id = self.stream_messages.get(streamer)
                    if message_id:
                        # Kanal auswählen basierend auf dem Streamer
                        channel = self.get_channel_for_streamer(streamer)

                        try:
                            message = await channel.fetch_message(message_id)
                            await message.delete()
                        except discord.NotFound:
                            print(f"Nachricht mit ID {message_id} wurde nicht gefunden.")
                        await self.delete_stream_message(streamer)
                        await self.save_streamer_status(streamer, False)

            self.streamers_live_status.update({streamer: is_live for streamer in watchlist})

        except Exception as e:
            print(f"Fehler beim Überprüfen der Streamer: {e}")

    def get_channel_for_streamer(self, streamer_name):
        special_streamers = {"nikonici1990": 1296476418342916096, "fraukratzig": 1296476418342916096}
        return self.bot.get_channel(special_streamers.get(streamer_name.lower(), 1296476471027568660))

    async def create_embed(self, stream_data, user_data):
        streamer_name = user_data['display_name']
        thumbnail_url = stream_data['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720')
        save_path = f'img/{streamer_name}.jpg'
        await self.download_image(thumbnail_url, save_path)
        file = discord.File(save_path, filename=f'{streamer_name}.jpg')
        if user_data['display_name'] in ["NikoNici1990", "FrauKratzig"]:
            embed = discord.Embed(title=f"{stream_data['title']}",
                                colour=discord.Color.from_rgb(0, 255, 255),
                                url=f"https://www.twitch.tv/{streamer_name}",
                                timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.set_author(name=f"{streamer_name} ist jetzt Live auf Twitch",
                            icon_url=f"{user_data['profile_image_url']}")
            embed.add_field(name="Spiel",
                            value=f"{stream_data['game_name']}",
                            inline=True)
            embed.add_field(name="Zuschauer",
                            value=f"{stream_data['viewer_count']}",
                            inline=True)
            embed.set_image(url=f"attachment://{streamer_name}.jpg")
            embed.set_thumbnail(url=user_data['profile_image_url'])
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                            icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        else:
            embed = discord.Embed(title=f"{stream_data['title']}",
                                colour=discord.Color.orange(),
                                url=f"https://www.twitch.tv/{streamer_name}",
                                timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.set_author(name=f"{streamer_name} ist jetzt Live auf Twitch",
                            icon_url=f"{user_data['profile_image_url']}")
            embed.add_field(name="Spiel",
                            value=f"{stream_data['game_name']}",
                            inline=True)
            embed.add_field(name="Zuschauer",
                            value=f"{stream_data['viewer_count']}",
                            inline=True)
            embed.set_image(url=f"attachment://{streamer_name}.jpg")
            embed.set_thumbnail(url=user_data['profile_image_url'])
            embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                            icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        return embed, file

    # Slash-Befehle
    @bridge.bridge_command(name="addstreamer", description="Streamer zur Watchlist hinzufügen")
    @bridge.has_permissions(administrator=True)
    @bridge.bridge_option("streamer_name", str, description="Name des Streamers")
    async def addstreamer_command(self, ctx, streamer_name):
        streamer_name = streamer_name.lower()
        if streamer_name not in self.watchlist:
            self.watchlist.append(streamer_name)
            await self.save_to_db('watchlist', [('INSERT OR IGNORE INTO watchlist VALUES (?)', (streamer_name,))])
            await ctx.respond(f"{streamer_name} wurde zur Watchlist hinzugefügt.")
        else:
            await ctx.respond(f"{streamer_name} ist bereits in der Watchlist.")

    @bridge.bridge_command(name="removestreamer", description="Streamer aus der Watchlist entfernen")
    @bridge.has_permissions(administrator=True)
    @bridge.bridge_option("streamer_name", str, description="Name des Streamers")
    async def removestreamer_command(self, ctx, streamer_name):
        streamer_name = streamer_name.lower()
        if streamer_name in self.watchlist:
            self.watchlist.remove(streamer_name)
            await self.save_to_db('watchlist', [('DELETE FROM watchlist WHERE streamer_name = ?', (streamer_name,))])
            await ctx.respond(f"{streamer_name} wurde aus der Watchlist entfernt.")
        else:
            await ctx.respond(f"{streamer_name} ist nicht in der Watchlist.")

# Setup
def setup(bot):
    bot.add_cog(Twitch(bot))

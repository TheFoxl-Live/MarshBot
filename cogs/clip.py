import datetime
import discord
import os
import aiohttp
import aiosqlite
from dotenv import load_dotenv
from discord.ext import commands, tasks


class TwitchClips(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_checked = datetime.datetime.utcnow()

        load_dotenv()

        self.TWITCH_CLIENT_ID =  os.getenv('CLIENT_ID')
        self.TWITCH_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        self.channel_name = "NikoNici1990"

        self.loop = self.bot.loop
        self.loop.run_until_complete(self.init_db())
        self.check_clips.start()

    async def init_db(self):
        async with aiosqlite.connect("marsh.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS clips (
                    id TEXT PRIMARY KEY,
                    url TEXT
                )
            ''')
            await db.commit()

    async def load_clips_posted(self):
        clips_posted = {}
        async with aiosqlite.connect("marsh.db") as db:
            async with db.execute("SELECT id, url FROM clips") as cursor:
                async for row in cursor:
                    clips_posted[row[0]] = row[1]
        return clips_posted

    async def save_clip_posted(self, clip_id, clip_url):
        async with aiosqlite.connect("marsh.db") as db:
            await db.execute("INSERT OR IGNORE INTO clips (id, url) VALUES (?, ?)", (clip_id, clip_url))
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
                data = await response.json()
                return data['access_token']

    async def get_clips(self, access_token, client_id, broadcaster_name):
        broadcaster_id = await self.get_broadcaster_id(access_token, client_id, broadcaster_name)
        url = f'https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}&started_at={self.last_checked.isoformat()}Z'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return data['data'] if data['data'] else None

    async def get_broadcaster_id(self, access_token, client_id, streamer_name):
        url = f'https://api.twitch.tv/helix/users?login={streamer_name}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return data['data'][0]['id'] if data['data'] else None


    async def create_clip_embed(self, clip):
        embed = discord.Embed(title=clip['title'],
                              url=clip['url'],
                              description=f"Erstellt von: {clip['creator_name']}",
                              color=discord.Color.purple(),
                              timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.set_author(name=f"» Neuer Clip", icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        embed.set_image(url=clip['thumbnail_url'])
        embed.set_footer(text="MarshmallowBot - Dein fluffiger Freund in der digitalen Welt!",
                    icon_url="https://nextcloud.universe-of-gaming.de/s/2EbH6G7tszkF8gE/preview")
        return embed

    @tasks.loop(minutes=2)  # Überprüft alle 5 Minuten auf neue Clips
    async def check_clips(self):
        try:
            access_token = await self.get_twitch_access_token(self.TWITCH_CLIENT_ID, self.TWITCH_CLIENT_SECRET)
            self.clips_posted = await self.load_clips_posted()  # Lädt die geposteten Clips aus der DB
            clips = await self.get_clips(access_token, self.TWITCH_CLIENT_ID, self.channel_name)

            if clips:
                channel = self.bot.get_channel(1129779878678495234)
                for clip in clips:
                    if clip['id'] not in self.clips_posted:
                        embed = await self.create_clip_embed(clip)
                        message = f"<:AmazedOctoEmote112:1036203998786633758> Es wurde ein neuer Clip erstellt:"
                        await channel.send(message)
                        await channel.send(embed=embed)
                        await self.save_clip_posted(clip['id'], clip['url'])

            self.last_checked = datetime.datetime.utcnow()  # Aktualisiert den letzten Überprüfungszeitpunkt
        except Exception as e:
            print(f"Fehler beim Abrufen der Clips: {e}")

def setup(bot):
    bot.add_cog(TwitchClips(bot))
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

class DiscordNotifier:
    def __init__(self):
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        
        # Set up all required intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.setup_bot()
        self.is_ready = False

    def setup_bot(self):
        @self.bot.event
        async def on_ready():
            print(f'Discord bot logged in as {self.bot.user}')
            self.is_ready = True

    async def send_notification(self, match_data):
        """
        Send a consolidated notification about a token and all its related news articles
        """
        # Wait for bot to be ready before sending messages
        while not self.is_ready:
            await asyncio.sleep(1)
            
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                print("Could not find Discord channel")
                return

            embed = discord.Embed(
                title="🔍 New Token-News Match Found!",
                color=discord.Color.green()
            )

            # Add token information
            token = match_data['token']
            token_info = (
                f"**Name:** {token['name']}\n"
                f"**Chain:** {token['platform']}\n"
                f"**Total Related Articles:** {match_data['total_matches']}"
            )
            
            if token.get('description'):
                token_info += f"\n\n**Description:** {token['description']}"
            
            if token.get('links'):
                token_info += "\n\n**Links:**"
                for link in token['links']:
                    token_info += f"\n• [{link.get('label', 'Link')}]({link.get('url')})"

            # Set thumbnail if token has an icon
            if token.get('icon'):
                embed.set_thumbnail(url=token['icon'])

            embed.add_field(
                name="Token Information",
                value=token_info,
                inline=False
            )

            # Add news summary
            news_summary = ""
            for idx, match in enumerate(match_data['matches'][:5], 1):
                news_summary += f"\n{idx}. {match['news']['title'][:100]}..."
            
            if len(match_data['matches']) > 5:
                news_summary += f"\n\n...and {len(match_data['matches']) - 5} more articles"

            embed.add_field(
                name="Related News Articles",
                value=news_summary if news_summary else "No articles found",
                inline=False
            )

            await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending Discord notification: {str(e)}")

    async def start(self):
        """
        Start the Discord bot
        """
        await self.bot.start(self.token)

    async def close(self):
        """
        Close the Discord bot connection
        """
        await self.bot.close()

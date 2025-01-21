import asyncio
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from news_scraper import NewsScraper
from token_scraper import TokenScraper
from discord_notifier import DiscordNotifier
import os

load_dotenv()

class CryptoNewsMonitor:
    def __init__(self):
        self.news_scraper = NewsScraper()
        self.token_scraper = TokenScraper()
        self.discord_notifier = DiscordNotifier()
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.8))

    def calculate_similarity(self, token_name, keywords):
        """
        Calculate similarity between token name and keywords
        """
        max_ratio = 0
        matched_keywords = []
        
        for keyword in keywords:
            ratio = fuzz.ratio(token_name.lower(), keyword.lower())
            if ratio > max_ratio:
                max_ratio = ratio
            if ratio >= self.similarity_threshold * 100:
                matched_keywords.append((keyword, ratio))

        return max_ratio / 100, matched_keywords

    async def check_matches(self):
        """
        Check for matches between news and tokens
        """
        try:
            print("\n🔄 Starting new monitoring cycle...")
            
            # Fetch new data
            news_items = await self.news_scraper.fetch_crypto_news()
            new_tokens = await self.token_scraper.fetch_new_tokens()

            if not news_items or not new_tokens:
                print("ℹ️ No data to compare, waiting for next cycle...")
                return

            print(f"\n🔍 Analyzing {len(new_tokens)} tokens against {len(news_items)} news articles")
            print("\n📊 Token Analysis:")
            
            # Look for matches
            matches_found = 0
            for token in new_tokens:
                token_name = token['name']
                print(f"\n   Token: {token_name}")
                print(f"   Chain: {token['platform']}")
                
                potential_matches = []
                for news_item in news_items:
                    similarity, matched_keywords = self.calculate_similarity(
                        token_name, 
                        news_item['keywords']
                    )

                    if similarity >= self.similarity_threshold and matched_keywords:
                        matches_found += 1
                        potential_matches.append({
                            'news': news_item,
                            'keywords': matched_keywords,
                            'similarity': similarity
                        })
                
                if potential_matches:
                    print(f"   ✨ Found {len(potential_matches)} relevant news articles:")
                    for idx, match in enumerate(potential_matches, 1):
                        print(f"      Article {idx}:")
                        print(f"      • Title: {match['news']['title'][:100]}...")
                        print(f"      • Matched: {', '.join(f'{kw[0]} ({kw[1]:.1f}%)' for kw in match['keywords'][:3])}")
                        if len(match['keywords']) > 3:
                            print(f"      • ...and {len(match['keywords']) - 3} more matches")
                    
                    # Send one consolidated notification for all matches
                    match_data = {
                        'token': token,
                        'matches': potential_matches,
                        'total_matches': len(potential_matches)
                    }
                    await self.discord_notifier.send_notification(match_data)
                else:
                    print("   ℹ️ No relevant news found")
            
            print(f"\n📈 Analysis complete: {matches_found} total matches found")

        except Exception as e:
            print(f"❌ Error in check_matches: {str(e)}")

    async def run(self):
        """
        Main run loop
        """
        try:
            print("\n🤖 Starting Discord bot...")
            discord_task = asyncio.create_task(self.discord_notifier.start())
            
            # Wait for Discord bot to be ready
            print("Waiting for Discord bot to connect...")
            while not self.discord_notifier.is_ready:
                await asyncio.sleep(1)
            print("Discord bot connected successfully!")

            # Schedule regular checks
            news_interval = int(os.getenv('NEWS_UPDATE_INTERVAL', 300))
            token_interval = int(os.getenv('TOKEN_UPDATE_INTERVAL', 300))
            check_interval = min(news_interval, token_interval)

            print(f"⏰ Monitoring cycle configured for every {check_interval} seconds")

            while True:
                await self.check_matches()
                
                # Countdown timer
                next_update = datetime.now() + timedelta(seconds=check_interval)
                while datetime.now() < next_update:
                    time_left = int((next_update - datetime.now()).total_seconds())
                    if time_left % 10 == 0:  # Update every 10 seconds
                        minutes = time_left // 60
                        seconds = time_left % 60
                        if minutes > 0:
                            print(f"\r⏳ Next update in: {minutes}m {seconds}s", end='', flush=True)
                        else:
                            print(f"\r⏳ Next update in: {seconds}s", end='', flush=True)
                    await asyncio.sleep(1)
                print("\r" + " " * 50 + "\r", end='', flush=True)  # Clear the countdown line

        except Exception as e:
            print(f"❌ Error in run loop: {str(e)}")
        finally:
            await self.discord_notifier.close()

if __name__ == "__main__":
    monitor = CryptoNewsMonitor()
    asyncio.run(monitor.run())

from web3 import Web3
import requests
import os
from dotenv import load_dotenv
import time
from collections import Counter
from nltk.tokenize import word_tokenize

load_dotenv()

class TokenScraper:
    def __init__(self):
        # Initialize connections to different DEXs/APIs
        self.w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
        self.last_check_time = time.time()
        self.dex_screener_url = 'https://api.dexscreener.com/token-profiles/latest/v1'
        self.session = requests.Session()

    async def fetch_new_tokens(self):
        """
        Fetch newly listed tokens from multiple sources
        """
        try:
            print("\n📥 Fetching new token listings...")
            
            # Fetch from DEX Screener API
            dex_tokens = await self._fetch_from_dex_screener()
            if dex_tokens:
                print("\n💎 DEX Screener Tokens:")
                for token in dex_tokens:
                    print(f"   • {token['name']} ({token['platform']})")
            
            # Fetch from CoinGecko API
            coingecko_tokens = await self._fetch_from_coingecko()
            if coingecko_tokens:
                print("\n🦎 CoinGecko Tokens:")
                for token in coingecko_tokens:
                    print(f"   • {token['name']} ({token['platform']})")
            
            # Combine tokens
            all_tokens = dex_tokens + coingecko_tokens
            
            if all_tokens:
                # Analyze token trends
                self.analyze_token_trends(all_tokens)
                
                # Process tokens
                processed_tokens = self._process_tokens(all_tokens)
                return processed_tokens
            else:
                print("\nℹ️ No new tokens found")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching tokens: {str(e)}")
            return []

    async def _fetch_from_coingecko(self):
        """
        Fetch new tokens from CoinGecko API
        """
        try:
            # CoinGecko's new tokens endpoint
            url = "https://api.coingecko.com/api/v3/coins/new"
            response = self.session.get(url)
            
            if response.status_code == 200:
                tokens_data = response.json()
                processed_tokens = []
                
                for token in tokens_data:
                    processed_tokens.append({
                        'name': token.get('name', ''),
                        'symbol': token.get('symbol', ''),
                        'address': '',  # CoinGecko doesn't provide contract address for new listings
                        'platform': token.get('asset_platform_id', 'unknown'),
                        'created_at': time.time(),
                        'description': '',
                        'icon': token.get('image', {}).get('large', ''),
                        'links': [],
                        'source': 'coingecko'
                    })
                
                return processed_tokens
            else:
                print(f"ℹ️ CoinGecko API returned status {response.status_code}")
                return []
        except Exception as e:
            print(f"ℹ️ CoinGecko API not available: {str(e)}")
            return []

    async def _fetch_from_dex_screener(self):
        """
        Fetch new tokens from DEX Screener API
        """
        try:
            response = self.session.get(self.dex_screener_url)
            if response.status_code == 200:
                tokens_data = response.json()
                processed_tokens = []
                
                # Process each token from DEX Screener
                for token in tokens_data:
                    name = token.get('description', '').split('\n')[0] if token.get('description') else ''
                    chain = token.get('chainId', '')
                    
                    if not name:  # Skip tokens without names
                        continue
                        
                    processed_tokens.append({
                        'name': name.strip(),
                        'symbol': '',  # DEX Screener doesn't provide symbol directly
                        'address': token.get('tokenAddress'),
                        'platform': chain,
                        'created_at': time.time(),
                        'description': token.get('description'),
                        'icon': token.get('icon'),
                        'links': token.get('links', []),
                        'source': 'dex_screener'
                    })
                
                return processed_tokens
            else:
                print(f"❌ DEX Screener API returned status code: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching from DEX Screener: {str(e)}")
            return []

    def analyze_token_trends(self, tokens):
        """
        Analyze trends in token names and metadata
        """
        # Collect data for analysis
        chains = Counter()
        themes = {
            'meme': 0,
            'ai': 0,
            'defi': 0,
            'gaming': 0,
            'politics': 0
        }
        keywords = Counter()
        
        # Keywords to track
        theme_keywords = {
            'meme': ['pepe', 'doge', 'meme', 'elon', 'wojak'],
            'ai': ['ai', 'artificial', 'intelligence', 'bot', 'gpt'],
            'defi': ['swap', 'yield', 'farm', 'dao', 'finance'],
            'gaming': ['play', 'game', 'nft', 'meta', 'world'],
            'politics': ['trump', 'biden', 'putin', 'president', 'vote']
        }
        
        for token in tokens:
            # Count chains
            chains[token['platform']] += 1
            
            # Analyze name for themes
            name_lower = token['name'].lower()
            
            # Count theme occurrences
            for theme, keywords_list in theme_keywords.items():
                if any(keyword in name_lower for keyword in keywords_list):
                    themes[theme] += 1
            
            # Extract words for keyword analysis
            words = word_tokenize(name_lower)
            for word in words:
                if word.isalnum() and len(word) > 2:
                    keywords[word] += 1
        
        # Display analysis
        print("\n📊 TOKEN TRENDS ANALYSIS")
        
        print("\n⛓️ Popular Chains:")
        for chain, count in chains.most_common():
            print(f"   • {chain}: {count} tokens")
        
        print("\n🎯 Token Themes:")
        for theme, count in themes.items():
            if count > 0:
                print(f"   • {theme.title()}: {count} tokens")
        
        print("\n🔤 Common Words in Token Names:")
        for word, count in keywords.most_common(10):
            print(f"   • {word}: {count} occurrences")

    def _process_tokens(self, tokens):
        """
        Process and filter token data
        """
        processed_tokens = []
        current_time = time.time()
        
        for token in tokens:
            # Only include tokens added since last check
            if 'created_at' in token and token['created_at'] > self.last_check_time:
                processed_tokens.append(token)
        
        if processed_tokens:
            print(f"\n✨ Total new tokens found: {len(processed_tokens)}")
        else:
            print("\nℹ️ No new tokens found since last check")
        
        self.last_check_time = current_time
        return processed_tokens

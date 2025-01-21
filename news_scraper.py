import os
import nltk
import requests
from collections import Counter
from datetime import datetime, timedelta
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
from dotenv import load_dotenv

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)

class NewsScraper:
    def __init__(self):
        """
        Initialize the news scraper with NewsAPI
        """
        load_dotenv()
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        
        self.base_url = "https://newsapi.org/v2/everything"
        self.top_headlines_url = "https://newsapi.org/v2/top-headlines"
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Add custom stop words
        self.stop_words.update(['said', 'says', 'would', 'could', 'may', 'might', 'will', 'year', 'today', 'according'])

    def _analyze_trending_topics(self, articles):
        """
        Analyze trending topics, names, and themes in articles
        """
        # Combine all text
        all_text = ' '.join([
            f"{article.get('title', '')} {article.get('description', '')}"
            for article in articles
        ])
        
        # Get named entities
        named_entities = self._extract_named_entities(all_text)
        
        # Get word frequencies
        word_freq = self._get_word_frequencies(all_text)
        
        # Get bigrams (two-word phrases)
        bigrams = self._get_bigrams(all_text)
        
        return named_entities, word_freq, bigrams

    def _extract_named_entities(self, text):
        """
        Extract named entities (people, organizations, locations)
        """
        entities = {
            'PERSON': Counter(),
            'ORGANIZATION': Counter(),
            'GPE': Counter()  # Geographical/Political Entities
        }
        
        # Process text in chunks to avoid memory issues
        sentences = sent_tokenize(text)
        for sentence in sentences:
            tokens = word_tokenize(sentence)
            tagged = pos_tag(tokens)
            named_ents = ne_chunk(tagged)
            
            for chunk in named_ents:
                if hasattr(chunk, 'label'):
                    if chunk.label() in entities:
                        name = ' '.join([token for token, pos in chunk.leaves()])
                        entities[chunk.label()][name] += 1
        
        return entities

    def _get_word_frequencies(self, text):
        """
        Get most frequent words
        """
        tokens = word_tokenize(text.lower())
        words = [
            self.lemmatizer.lemmatize(word)
            for word in tokens
            if word.isalnum() and 
            word not in self.stop_words and 
            len(word) > 2
        ]
        return Counter(words)

    def _get_bigrams(self, text):
        """
        Get most common two-word phrases
        """
        tokens = word_tokenize(text.lower())
        clean_tokens = [
            self.lemmatizer.lemmatize(word)
            for word in tokens
            if word.isalnum() and 
            word not in self.stop_words and 
            len(word) > 2
        ]
        
        bigrams = list(zip(clean_tokens[:-1], clean_tokens[1:]))
        return Counter([' '.join(bigram) for bigram in bigrams])

    def _display_trending_analysis(self, named_entities, word_freq, bigrams):
        """
        Display trending analysis in a formatted way
        """
        print("\n📊 TRENDING ANALYSIS")
        print("\n👥 Top Mentioned People:")
        for person, count in named_entities['PERSON'].most_common(5):
            print(f"   • {person} ({count} mentions)")

        print("\n🏢 Top Organizations:")
        for org, count in named_entities['ORGANIZATION'].most_common(5):
            print(f"   • {org} ({count} mentions)")

        print("\n📍 Top Locations:")
        for location, count in named_entities['GPE'].most_common(5):
            print(f"   • {location} ({count} mentions)")

        print("\n🔤 Most Used Words:")
        for word, count in word_freq.most_common(10):
            print(f"   • {word} ({count} times)")

        print("\n🔠 Trending Phrases:")
        for phrase, count in bigrams.most_common(5):
            print(f"   • {phrase} ({count} times)")

    async def fetch_crypto_news(self):
        """
        Fetch news from multiple categories including worldwide and trending news
        """
        try:
            print("\n📰 Fetching news articles...")
            all_articles = []
            
            # Fetch top headlines
            top_news = self._fetch_top_headlines()
            if top_news:
                print("\n🔥 Top Headlines:")
                for article in top_news[:3]:  # Show sample of top headlines
                    print(f"   • {article['title']}")
                all_articles.extend(top_news)
            
            # Fetch crypto-related news
            crypto_news = self._fetch_crypto_news()
            if crypto_news:
                print("\n💰 Crypto News:")
                for article in crypto_news[:3]:  # Show sample of crypto news
                    print(f"   • {article['title']}")
                all_articles.extend(crypto_news)
            
            # Fetch general worldwide news
            world_news = self._fetch_world_news()
            if world_news:
                print("\n🌍 World News:")
                for article in world_news[:3]:  # Show sample of world news
                    print(f"   • {article['title']}")
                all_articles.extend(world_news)
            
            # Analyze trending topics
            named_entities, word_freq, bigrams = self._analyze_trending_topics(all_articles)
            self._display_trending_analysis(named_entities, word_freq, bigrams)
            
            # Process all articles
            processed_articles = []
            for article in all_articles:
                if article and article.get('title') and article.get('description'):
                    keywords = self._extract_keywords(
                        f"{article['title']} {article['description']}"
                    )
                    if keywords:
                        processed_articles.append({
                            'title': article['title'],
                            'description': article['description'],
                            'url': article['url'],
                            'published_at': article['publishedAt'],
                            'keywords': keywords
                        })
            
            print(f"\n✨ Total articles processed: {len(processed_articles)}")
            return processed_articles

        except Exception as e:
            print(f"❌ Error fetching news: {str(e)}")
            return []

    def _fetch_top_headlines(self, country='us'):
        """
        Fetch top headlines
        """
        try:
            params = {
                'apiKey': self.api_key,
                'country': country,
                'pageSize': 20
            }
            response = requests.get(self.top_headlines_url, params=params)
            if response.status_code == 200:
                return response.json().get('articles', [])
            return []
        except Exception as e:
            print(f"❌ Error fetching top headlines: {str(e)}")
            return []

    def _fetch_crypto_news(self):
        """
        Fetch crypto-related news
        """
        try:
            params = {
                'apiKey': self.api_key,
                'q': 'cryptocurrency OR bitcoin OR blockchain',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20
            }
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                return response.json().get('articles', [])
            return []
        except Exception as e:
            print(f"❌ Error fetching crypto news: {str(e)}")
            return []

    def _fetch_world_news(self):
        """
        Fetch general worldwide news
        """
        try:
            params = {
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'popularity',
                'pageSize': 20,
                'domains': 'bbc.co.uk,reuters.com,apnews.com,bloomberg.com'
            }
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                return response.json().get('articles', [])
            return []
        except Exception as e:
            print(f"❌ Error fetching world news: {str(e)}")
            return []

    def _extract_keywords(self, text):
        """
        Extract and process keywords from text
        """
        try:
            # Tokenize and clean text
            tokens = word_tokenize(text.lower())
            
            # Remove stop words and short words
            tokens = [
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if token.isalnum() and 
                token not in self.stop_words and 
                len(token) > 2
            ]
            
            # Get word frequency
            word_freq = nltk.FreqDist(tokens)
            
            # Return top keywords
            return list(word_freq.keys())

        except Exception as e:
            print(f"❌ Error extracting keywords: {str(e)}")
            return []

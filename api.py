import os
from app import app, Request,JSONResponse,APIRouter,HTTPException, Depends
from datetime import datetime
from datetime import timedelta
from datetime import date
from requests_cache import CachedSession
import pprint
import dateutil.parser
import feedparser
from dotenv import load_dotenv
import proxies.deeplcom as deeplcom
import sqlite3
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import *

DATABASE= 'articles.db'
load_dotenv()
pp = pprint.PrettyPrinter(indent=4,width=120)
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=timedelta(hours=1))
api = APIRouter()

rss_feed = [
    # United States
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.washingtonpost.com/rss/world",
    "https://rssfeeds.usatoday.com/usatoday-NewsTopStories",
    "https://www.latimes.com/rss2.0.xml",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    
    # United Kingdom
    "https://www.theguardian.com/world/rss",
    "https://www.thetimes.co.uk/rss",
    "https://www.dailymail.co.uk/articles.rss",
    "https://www.independent.co.uk/rss",
    "https://www.ft.com/news-feed?format=rss",
    
    # Canada
    "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "https://www.thestar.com.my/rss/News",
    "https://nationalpost.com/rss.xml",
    "https://www.ledevoir.com/rss/manchettes.xml",
    "https://www.lapresse.ca/manchettes/rss",
    
    # Australia
    "https://www.smh.com.au/rss/feed.xml",
    "https://www.theage.com.au/rss/feed.xml",
    "https://www.theaustralian.com.au/feeds/rss",
    "https://www.heraldsun.com.au/feeds/rss",
    "https://www.brisbanetimes.com.au/rss/feed.xml",
    
    # Germany
    "https://www.faz.net/rss/aktuell/",
    "https://rss.sueddeutsche.de/rss/topthemen",
    "https://www.welt.de/feeds/latest.rss",
    "https://www.handelsblatt.com/contentexport/feed/top-themen",
    "https://www.spiegel.de/schlagzeilen/tops/index.rss",
    
    # France
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    "https://www.liberation.fr/arc/outboundfeeds/rss-all/?outputType=xml",
    "https://feeds.leparisien.fr/leparisien/rss",
    "https://services.lesechos.fr/rss/les-echos-monde.xml"
]

@api.get('/translate/{lang}')
def api_translate(request: Request, lang: str):
    res=[]
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()    
    c.execute('''
        SELECT a.id article_id, t.id translation_id, a.paper, t.title t_title, a.image, a.link, 
                t.description t_description, a.published,
                a.description a_description,
                a.title a_title
        FROM articles a
        LEFT JOIN translations t ON a.id = t.article_id
        WHERE strftime('%Y-%m-%d', published) = date(?)
        AND (t.language_code = ? OR t.language_code ISNULL)''', (date.today(),lang,))
    rows = c.fetchall()
    columns = [column[0] for column in c.description]  
    for row in rows:
        row = dict(zip(columns, row))
        title       = row['t_title']
        description = row['t_description']
        pubdate = dateutil.parser.parse(row['published'])
        print(row['article_id'],row['a_title'],row['a_description'],lang)
        if row['translation_id'] is None:
            value       = insert_translation(row['article_id'],row['a_title'],row['a_description'],lang)
            title       = value[1]
            description = value[2]
        article = {
            "paper"      : row['paper'],
            "title"      : title,
            "image"      : row['image'],
            "link"       : row['link'],
            "description": description,
            "published": pubdate.strftime("%d %b %Y %H:%M"),
        }
        res.append(article)     
    conn.close()
    return res

@api.get('/feed')
def api_feed(request: Request):
    create_table()
    res = []
    titles = []
    for feed in rss_feed:
        from_cache = ''
        try:
            response = session.get(feed, timeout=10)
            from_cache = response.from_cache
        except Exception as exc:
            print('Error:', feed)
            from_cache = exc
        rss_xml = response.content.decode(response.apparent_encoding)
        rss = feedparser.parse(rss_xml)
        articles_nbr = len(rss.entries)
        print(str(from_cache).ljust(6), f'{articles_nbr:03d}',feed)
        for ent in rss.entries:
            image = ''
            description = ''
            try:
                description = ent.description
            except:
                pass            
            try:
                image = ent.media_content[0]['url']
            except:
                try:
                    image = ent.enclosure
                except:
                    pass
            if image == '':
                continue
            if ent.title in titles:
                continue
            soup    = BeautifulSoup(description)
            paper   = urlparse(feed).netloc.replace('www.','').replace('rss.','')
            pubdate = dateutil.parser.parse(ent.published)
            article = {
                "paper": paper,
                "title": truncate_string(ent.title,100),
                "image": image,
                "description": truncate_string(soup.get_text()),
                "link": ent.link,
                "published": pubdate,
            }
            insert_article(article)
            res.append(article)
            #result = client.collection("news").create(article)
            # print(res)
    return res

app.include_router(api, prefix="/api") 


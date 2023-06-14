import os
import ipaddress
from app import app, Request,JSONResponse,APIRouter,HTTPException, Depends
from datetime import datetime
from datetime import timedelta
from datetime import date
from requests_cache import CachedSession
from starlette.concurrency import run_in_threadpool
import pprint
import dateutil.parser
import feedparser
from dotenv import load_dotenv
import proxies.deeplcom as deeplcom
import sqlite3
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import *

load_dotenv()
pp = pprint.PrettyPrinter(indent=4,width=120)
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=timedelta(hours=1))
api = APIRouter()

def check_localhost(request: Request):
    allowed_ip_range_str = os.getenv("ALLOWED_IP_RANGE")
    client_ip = request.client.host
    if allowed_ip_range_str:
        allowed_ip_ranges = allowed_ip_range_str.split(',')
        for ip_range in allowed_ip_ranges:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip_range):
                return
        raise HTTPException(status_code=403, detail="Access restricted")
    else:
        raise HTTPException(status_code=500, detail="Allowed IP range not defined in .env")

@api.get('/translate/{lang}')
def api_translate(request: Request, lang: str):
    check_localhost(request)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    res=[]
    c.execute("SELECT * FROM articles WHERE date(published) >= datetime('now','-24 hour')")
    rows = c.fetchall()
    columns = [column[0] for column in c.description]  
    for row in rows:
        row = dict(zip(columns, row))
        sql = "SELECT title,description FROM translations WHERE article_id=? AND language_code=?"
        c.execute(sql, (row['id'],lang,))  
        translation = c.fetchone()
        if translation:
            continue
        id = row['id']
        title       = row['title']
        description = row['description']
        pubdate     = dateutil.parser.parse(row['published'])
        value       = insert_translation(id,title,description,lang)
        title       = value[1]
        description = value[2]
        article = {
            "paper"      : row['paper'],
            "feed_id"    : row['feed_id'],            
            "title"      : title,
            "image"      : row['image'],
            "link"       : row['link'],
            "description": description,
            "published"  : pubdate.strftime("%d %b %Y %H:%M"),
        }
        res.append(article)     
    conn.close()
    return res

@api.get('/feed')
async def api_feed(request: Request):
    check_localhost(request)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    create_table()
    res = []
    titles = []
    c.execute("SELECT * FROM feeds")
    rows = c.fetchall()
    columns = [column[0] for column in c.description]      
    for row in rows:
        row = dict(zip(columns, row))
        from_cache = ''
        response = None
        try:
            response = session.get(row['link'], timeout=10)
            from_cache = response.from_cache
        except Exception as exc:
            print('Error:', row['link'])
            from_cache = exc
        if response == None:
            continue
        rss_xml = response.content.decode(response.apparent_encoding)
        rss = feedparser.parse(rss_xml)
        for ent in rss.entries:
            if ent.title in titles or not hasattr(ent, 'published'):
                continue
            image = ''
            image_file = ''
            description = ''
            paper   = urlparse(row['link']).netloc.replace('www.','').replace('rss.','')
            pubdate = dateutil.parser.parse(ent.published)
            if hasattr(ent, 'media_thumbnail') and ent.media_thumbnail[0]:
                image = ent.media_thumbnail[0]['url']
            elif hasattr(ent, 'media_content') and ent.media_content[0]:
                image = ent.media_content[0]['url']
            elif hasattr(ent, 'enclosure'):
                image = ent.enclosure
            if hasattr(ent, 'description'):
                description = ent.description
                soup = BeautifulSoup(description,features="html.parser")
                if image == '':
                    img_tag = soup.find('img')
                    if img_tag:
                        image = img_tag['src']
                description = soup.get_text()
            
            if image == '' and hasattr(ent, 'content'):
                if  'value' in ent.content[0]:
                    soup = BeautifulSoup(ent.content[0]['value'],features="html.parser")
                    img_tag = soup.find('img')
                    if img_tag:
                        image = img_tag['src']     

            if image != '':
                image_file = os.path.basename(image).split("?")[0]
                image_path = 'static/images/'+image_file
                if not os.path.isfile(image_path):
                    rst = await run_in_threadpool(download_image, image, image_path)

            article = {
                "paper": paper,
                "feed_id": row['id'],
                "title": truncate_string(ent.title,100),
                "image": image_file,
                "description": truncate_string(description),
                "link": ent.link,
                "published": pubdate,
            }
            insert_article(article)
            res.append(article)
            if image != '':
                update_article({"image": image_file,"link": ent.link})
                print(paper, {"image": image_file,"link": ent.link})
    return res

app.include_router(api, prefix="/api") 


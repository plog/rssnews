import os
import ipaddress
from app import app, Request,JSONResponse,APIRouter,HTTPException, Depends
from datetime import datetime
from datetime import timedelta
from datetime import date
from requests_cache import CachedSession
import pprint
import dateutil.parser
import feedparser
from dotenv import load_dotenv
import proxies.chatgpt as chatgpt
import sqlite3
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import *

load_dotenv()
pp = pprint.PrettyPrinter(indent=4,width=120)
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=timedelta(hours=1))
api = APIRouter()
image_extensions = ['.jpg', '.jpeg', '.png', '.gif']

def check_localhost(request: Request):
    allowed_ip_range_str = os.getenv("ALLOWED_IP_RANGE")
    client_ip = request.client.host
    if allowed_ip_range_str:
        allowed_ip_ranges = allowed_ip_range_str.split(',')
        for ip_range in allowed_ip_ranges:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip_range):
                return
        raise HTTPException(status_code=403, detail=client_ip+": Access restricted")
    else:
        raise HTTPException(status_code=500, detail=client_ip+": Not defined in .env")

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
        id          = row['id']
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

@api.get('/select/{feed}')
def api_select(request: Request, feed: str):
    gpt = chatgpt.ChatGPT()
    conn = sqlite3.connect(DATABASE)
    create_table()
    c = conn.cursor()
    sql = """
        SELECT a.* FROM articles a 
        JOIN feeds f ON f.id = a.feed_id
        WHERE feed_id = ?
    """
    c.execute(sql, (feed,))
    rows = c.fetchall()
    columns = [column[0] for column in c.description]
    res = []
    for row in rows:
        row = dict(zip(columns, row))
        article = {"id": row['id'],"title": row['title']}
        res.append(article)
    res  = gpt.select(res)
    print(res)
    for article in res:
        sql = "UPDATE articles SET score=?, keywords=? WHERE id=?"
        c.execute(sql, (int(article['score']), article['keywords'],int(article['id']),))
    conn.commit()
    conn.close()
    return res

@api.get('/feed')
def api_feed(request: Request):
    check_localhost(request)
    res = import_feed()
    return res

app.include_router(api, prefix="/api") 


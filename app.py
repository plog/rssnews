import feedparser
import os,json, sqlite3
import pprint
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from datetime import date
import dateutil.parser
from dotenv import load_dotenv
from requests_cache import CachedSession
from fastapi import FastAPI,Depends, status, Form, APIRouter,HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response,JSONResponse
from urllib.parse import urlparse


load_dotenv()
DATABASE= 'articles.db'
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv('SECRET'))
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static") 

pp = pprint.PrettyPrinter(indent=4,width=120)
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=timedelta(hours=1))

@app.get('/{lang}', include_in_schema=False)
def api_home(request: Request, lang:str):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()    
    c.execute('''
        SELECT a.id, t.id, a.paper, t.title t_title, a.image, a.link, 
                t.description t_description, a.published,
                a.description a_description,
                a.title a_title
        FROM articles a
        LEFT JOIN translations t ON a.id = t.article_id
        WHERE strftime('%Y-%m-%d', published) = date(?)
        AND (t.language_code = ? OR t.language_code ISNULL)''', (date.today(),lang,))  
    columns = [column[0] for column in c.description]  
    rows = c.fetchall()
    res = []
    for row in rows:
        row = dict(zip(columns, row))
        pubdate = dateutil.parser.parse(row['published'])
        article = {
                "paper": row['paper'].capitalize(),
                "title": row['t_title'],
                "image": row['image'],
                "description": row['t_description'],
                "link": row['link'],
                "published": pubdate.strftime("%d %b %Y"),
            }
        res.append(article) 
    context = {"request" : request, 'articles': res}   
    return templates.TemplateResponse("home.html", context=context, media_type="text/html")

# All requests   
# ------------ 
@app.middleware("http")
async def add_samesite_to_cookies(request, call_next):
    response = await call_next(request)
    if "set-cookie" in response.headers:
        cookies = response.headers["set-cookie"].split(", ")
        for i in range(len(cookies)):
            if "; samesite=" not in cookies[i]:
                cookies[i] += "; samesite=lax"
        response.headers["set-cookie"] = ", ".join(cookies)     
    return response

import api 
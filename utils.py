import sqlite3
import os
import shutil
import requests
import pprint
import feedparser
import dateutil.parser
from datetime import timedelta
from urllib.parse import urlparse
from requests_cache import CachedSession
import proxies.deeplcom as deeplcom
import proxies.chatgpt as chatgpt
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup

DATABASE= os.getenv('DATABASE')
image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
pp = pprint.PrettyPrinter(indent=4,width=120)
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=timedelta(hours=1))


def download_image(image_url, image_path):
    extension = os.path.splitext(image_url)[-1]
    if extension.lower() not in ['','.jpg','.jpeg','.png','.gif']:
        return 'no-img.png'
    img_res = requests.get(image_url, stream=True)
    with open(image_path, 'wb') as f:
        shutil.copyfileobj(img_res.raw, f)
    image = Image.open(image_path)
    image.thumbnail((400, 400))
    file_name, file_extension = os.path.splitext(image_path)
    if file_extension.lower() == '.png':
        image = image.convert('RGB')
    if file_extension.lower() == '':
        image_path = file_name+'.jpg'
    image.save(image_path)
    return os.path.basename(image_path)

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = '''CREATE TABLE IF NOT EXISTS articles (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               feed_id INTEGER,
               paper VARCHAR(255),
               title VARCHAR(255),
               image VARCHAR(255),
               description TEXT,
               link TEXT,
               score INTENGER,
               keywords TEXT,
               published DATETIME,
               CONSTRAINT unique_title UNIQUE (title),
               CONSTRAINT unique_link UNIQUE (link),
               CONSTRAINT unique_description UNIQUE (description)
    )'''
    c.execute(query)
    conn.commit()

    query = '''CREATE TABLE IF NOT EXISTS translations (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               article_id INTEGER,
               language_code VARCHAR(5),
               title VARCHAR(255),
               description TEXT,
               FOREIGN KEY (article_id) REFERENCES articles(id)
    )'''
    c.execute(query)    
    conn.commit()

    query = '''CREATE TABLE IF NOT EXISTS feeds (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               link TEXT,
               title VARCHAR(255),
               country CHAR(2),
               category VARCHAR(255),
               CONSTRAINT unique_link UNIQUE (link)
    )'''
    c.execute(query)
    conn.commit()


    conn.close()

def insert_article(article):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = '''INSERT INTO articles (paper, feed_id,title, image, description, link, published) VALUES (?, ?, ?, ?, ?, ?, ?)'''
    values = (
        article['paper'],
        article['feed_id'],
        article['title'],
        article['image'],
        article['description'],
        article['link'],
        article['published']
    )
    try:
        c.execute(query, values)
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def update_article(article):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = "UPDATE articles SET image=? WHERE link=?"
    values = (article['image'],article['link'])
    c.execute(query, values)
    conn.commit()
    conn.close()    

def insert_translation(article_id,title,description,lang):
    conn = sqlite3.connect(DATABASE)
    trans = chatgpt.ChatGPT()
    c = conn.cursor()
    query = '''DELETE FROM translations WHERE article_id = ?'''
    c.execute(query, (int(article_id),))
    conn.commit()
    query = '''INSERT INTO translations (article_id,title,description,language_code) VALUES (?,?,?,?)'''
    trans_title = trans.translate(title,lang)
    trans_descr = trans.translate(description,lang)
    # print("TITLE",lang,title,trans_title)
    # print("DESC",lang,description,trans_descr)
    values = (
        article_id,
        trans_title,
        trans_descr,
        lang,)
    try:
        c.execute(query, values)
        conn.commit()
        conn.close()
        return values        
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return None

def import_feed():
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
            # image_file = ''
            description = ''
            paper   = urlparse(row['link']).netloc.replace('www.','').replace('rss.','')
            pubdate = dateutil.parser.parse(ent.published)

            if hasattr(ent, 'links'):
                for link in ent.links:
                    if 'type' in link and 'image' in link['type']:
                        image = link['href']
            elif hasattr(ent, 'media_thumbnail') and ent.media_thumbnail[0]:
                image = ent.media_thumbnail[0]['url']
            elif hasattr(ent, 'media_content'):
                for media in ent.media_content:                       
                    if 'url' in media:
                        file_extension = os.path.splitext(media['url'])[1].lower()
                        if file_extension in image_extensions:
                            image = media['url']                       
                    if 'image' in media:
                        image = media['url']
                    if 'type' in media and 'image' in media['type']:
                        image = media['url']
            elif hasattr(ent, 'enclosure'):
                image = ent.enclosure
            elif hasattr(ent, 'description'):
                description = ent.description
                soup = BeautifulSoup(description,features="html.parser")                
                if image == '':                    
                    img_tag = soup.find('img')                     
                    if img_tag:
                        image = img_tag['src'].split("?")[0]                       
                description = soup.get_text()          
            elif image == '' and hasattr(ent, 'content'):
                for content in ent.content:
                    if  'value' in content:
                        soup = BeautifulSoup(content['value'],features="html.parser")
                        img_tag = soup.find('img')                  
                        if img_tag:
                            image = img_tag['src']
            # if image != '':
            #     image_file = os.path.basename(image).split("?")[0]
            #     image_path = 'static/images/'+image_file
            #     if not os.path.isfile(image_path):
            #         image = download_image(image, image_path)
            #     else:
            #         image = image_file
            # else:
            #     image = 'no-img.png'

            if image == '':
                image = 'no-img.png'
            article = {
                "paper": paper,
                "feed_id": row['id'],
                "title": truncate_string(ent.title,100),
                "image": image,
                "description": truncate_string(description),
                "link": ent.link,
                "published": pubdate,
            }
            insert_article(article)
            res.append(article)
            if image != '':                 
                update_article({"image": image,"link": ent.link})
            conn.commit()
    conn.close()
    return res            


def truncate_string(text, max_length=200):
    if len(text) <= max_length:
        return text
    else:
        truncated_text = text[:max_length].rsplit(' ', 1)[0]
        return truncated_text + '...'

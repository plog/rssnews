import sqlite3
import os
import shutil
import requests
import proxies.deeplcom as deeplcom
import proxies.chatgpt as chatgpt
from pathlib import Path
from PIL import Image

DATABASE= os.getenv('DATABASE')
image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']


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

#def get_feed():

def truncate_string(text, max_length=200):
    if len(text) <= max_length:
        return text
    else:
        truncated_text = text[:max_length].rsplit(' ', 1)[0]
        return truncated_text + '...'

import sqlite3
import os
import shutil
import requests
import proxies.deeplcom as deeplcom

DATABASE= os.getenv('DATABASE')

def download_image(image_url, image_path):
    img_res = requests.get(image_url, stream=True)
    with open(image_path, 'wb') as f:
        shutil.copyfileobj(img_res.raw, f)

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
    query = '''INSERT INTO articles (paper, feed_id,title, image, description, link, published)
               VALUES (?, ?, ?, ?, ?, ?, ?)'''
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
    trans = deeplcom.Deepl()
    c = conn.cursor()
    query = '''DELETE FROM translations WHERE article_id = ?'''
    c.execute(query, (int(article_id),))
    conn.commit()
    query = '''INSERT INTO translations (article_id,title,description,language_code) VALUES (?,?,?,?)'''
    values = (
        article_id,
        trans.translate(title,'',lang,True)[0],
        trans.translate(description,'',lang,True)[0],
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

def truncate_string(text, max_length=200):
    if len(text) <= max_length:
        return text
    else:
        truncated_text = text[:max_length].rsplit(' ', 1)[0]
        return truncated_text + '...'

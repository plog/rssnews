#!/usr/bin/env python
import os,sys,pathlib, sqlite3
import openai
import ast
import re

parent = pathlib.Path(__file__).parent.parent.resolve()
parent = os.path.abspath(parent)
sys.path.insert(1, parent)

import json,pprint,requests
import urllib.parse
from dotenv import load_dotenv
from requests_cache import CachedSession
load_dotenv()

pp = pprint.PrettyPrinter(indent=4,width=120)
openai.api_key = os.getenv('GPT_API')
engine = 'text-davinci-003'
language_dict = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "id": "Indonesian",
}
class ChatGPT():

    def select(self,news):
        prefix = """
 Sort the Python list of dict at the end of this prompt containing news headlines by impact on society.'
 For each news the dict must have the following structure:{"id":...,score":...,"keywords":...}
 "score" is a 1 to 10 (10=big impact) to determine the potential impact on people's lives, the ecosystem and the society.
 Wars, geopolitical tensions, large financial crisis or people dying always get 10.
 "keyword" should be a string of keywords separated by a comma capturing the essence of the news and its potential consequences. 
 Identify a keyword that best represents the news title and its impact. 
 Return ONLY the Python list of dict with the 5 most important news based on score above.
        """
        prefix += pprint.pformat(news)
        print(150*'-')
        print(prefix)
        print(150*'-')
        response = openai.Completion.create(
            model=engine,
            prompt=prefix,
            temperature=0.7,
            max_tokens=2000,
            frequency_penalty=0,
            presence_penalty=0
        )
        translated_text = ''
        translated_text = ''
        if choices := response.get('choices', []):
            if len(choices) > 0:
                translated_text = choices[0]['text']
        res = translated_text.strip()
        pattern = r"\[.*?\]"
        match = re.search(pattern, res, re.DOTALL)
        if match:
            res = eval(match.group())
        else:
            res = []        
        print(res)
        print(150*'+')
        return res
    
    def score(self,news):
        prefix =  f'Can you translate each "title" and "description" of the following Python list in {language_dict[to_lang]}.'
        prefix += f'fSend me the translated Python list. No other code or any other text: '
        prefix += str(news)
        print(150*'-')
        print(prefix)
        print(150*'-')
        response = openai.Completion.create(
            model=engine,
            prompt=prefix,
            temperature=0.7,
            max_tokens=900,
            frequency_penalty=0,
            presence_penalty=0
        )
        translated_text = ''
        translated_text = ''
        if choices := response.get('choices', []):
            if len(choices) > 0:
                translated_text = choices[0]['text']
        res = ast.literal_eval(translated_text.strip())
        return res
    
    def translate(self,search_term, to_lang):
        translations = []
        prefix =  f'Can you translate each "title" and "description" of the following Python list in {language_dict[to_lang]}.'
        prefix += f'fSend me the translated Python list. No other code or any other text: '
        prefix += str(search_term)
        print(150*'-')
        print(prefix)
        print(150*'-')
        response = openai.Completion.create(
            model=engine,
            prompt=prefix,
            temperature=0.7,
            max_tokens=900,
            frequency_penalty=0,
            presence_penalty=0
        )
        translated_text = ''
        if choices := response.get('choices', []):
            if len(choices) > 0:
                translated_text = choices[0]['text']
        res = ast.literal_eval(translated_text.strip())
        return res

if __name__ == "__main__":
    lex = ChatGPT()
    texts = [
        {
            "id": 5020,
            "paper": "nytimes.com",
            "title": "The Radical Strategy Behind Trump’s Promise to ‘Go After’ Biden",
            "description": "Conservatives with close ties to Donald J. Trump are laying out a “paradigm-shifting” legal rationale to erase the Justice Department’s independence from the president."
        },
        {
            "id": 5021,
            "paper": "nytimes.com",
            "title": "In Miami, the Only Violence From Trump Supporters Was Rhetorical",
            "description": "Calls for retribution were plentiful after the former president’s indictments, but the demonstrations proved tame, a possible result of the aggressive prosecution of the Jan. 6 rioters."
        },
        {
            "id": 5023,
            "paper": "nytimes.com",
            "title": "TikTok, Shein and Other Companies Distance Themselves From China",
            "description": "Companies are moving headquarters and factories outside the country and cleaving off their Chinese businesses. It’s not clear the strategy will work."
        },
        {
            "id": 4484,
            "paper": "theglobeandmail.com",
            "title": "I want to move internally, but my boss is unsupportive. What can I do?",
            "description": "I think he’s trying to sabotage my career progression so he doesn’t have to put the effort into replacing me"
        },
        {
            "id": 4926,
            "paper": "faz.net",
            "title": "Erste Kritik an EZB-Zinserhöhungen",
            "description": "Im vergangenen Jahr, als die Inflationsraten im Euroraum mehr als 10 Prozent betrugen, gab es eine sehr breite Zustimmung zu den Zinserhöhungen der EZB. Nun fordern Gewerkschaften und auch viele..."
        },
        {
            "id": 4316,
            "paper": "rssfeeds.usatoday.com",
            "title": "COVID's lasting effects: For many, wine tastes like water and smoke smells like clean air",
            "description": "A new study based on a 2021 national survey found more than 6 million people reported sensory loss as of that year.\n     "
        },
        {
            "id": 4832,
            "paper": "wired.com",
            "title": "10 Best Wi-Fi Routers (2023): Budget, Gaming Routers, Large Homes, Mesh",
            "description": "Don’t suffer the buffer. These WIRED-tested systems will deliver reliable internet across your home whatever your needs or budget."
        },
        {
            "id": 5058,
            "paper": "rssfeeds.usatoday.com",
            "title": "Quarterly taxes due date is coming up. Here's what you should know",
            "description": "For some, tax season feels like a yearlong event because they pay estimated taxes every quarter. The next payment is due June 15 or face penalties.\n     "
        },
        {
            "id": 4444,
            "paper": "theglobeandmail.com",
            "title": "Raymond James head of banking in Canada departs to join private credit firm Stonebridge Financial",
            "description": "Daniel Simunac will share the CEO title with Cam Di Giorgio at Stonebridge"
        },
        {
            "id": 4846,
            "paper": "feeds.a.dj.com",
            "title": "Shell's New Strategy Avoids the Toughest Questions",
            "description": "The European energy major promises stable oil and gas production this decade, but higher hurdles for investments in lower-carbon alternatives."
        },
        {
            "id": 5121,
            "paper": "theguardian.com",
            "title": "‘I have not seen one cent’: billions stolen in wage theft from US workers",
            "description": "Employees across the country are not getting paid what they’re owed, and critics say government is toothless to helpJose Martinez worked for a construction contractor in New York City for six months..."
        },
        {
            "id": 5094,
            "paper": "theguardian.com",
            "title": "Canada freezes ties with Chinese bank AIIB over claim it is ‘dominated by Communist party’",
            "description": "Finance minister announces immediate review of Canada’s involvement with Beijing’s alternative to the World BankCanada is freezing its ties with the China-led Asian Infrastructure Investment Bank..."
        },
        {
            "id": 4352,
            "paper": "theguardian.com",
            "title": "About 100 wedding guests feared dead as boat capsizes in northern Nigeria",
            "description": "Victims, including women and children, were reportedly returning from  ceremony A boat carrying residents returning from a wedding capsized in northern Nigeria killing about 100 people, police and..."
        }        
        ]
    res = lex.select(texts)
    pprint.pprint(res)
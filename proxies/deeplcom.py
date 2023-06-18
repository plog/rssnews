#!/usr/bin/env python
import os,sys,pathlib
parent = pathlib.Path(__file__).parent.parent.resolve()
parent = os.path.abspath(parent)
sys.path.insert(1, parent)

import json,pprint,requests
import urllib.parse
from dotenv import load_dotenv
from requests_cache import CachedSession
load_dotenv()

pp = pprint.PrettyPrinter(indent=4,width=120)
api_key   = os.getenv('DEEPL_KEY')
cache_req = os.getenv('REQUEST_CACHE')
session = CachedSession(cache_req, backend='filesystem',allowable_methods=['GET', 'POST'],expire_after=50)

class Deepl():
    def translate(self,search_term,source_lang, lang, detect_source=False):
        translations = []
        lang = lang.upper()
        url = "https://api.deepl.com/v2/translate"
        headers = {'Authorization': 'DeepL-Auth-Key ' + api_key}
        if detect_source:
            data = {'text':search_term,'target_lang':lang}            
        else:
            data = {'text':search_term,'source_lang':source_lang.upper(),'target_lang':lang}
        response = session.post(url, headers=headers, data=data)
        print(response)
        search = json.loads(response.text)

        try:
            for tr in search['translations']:
                translations.append(tr['text'])
        except Exception as e:
            print('error',search_term,source_lang, lang, e)
        return translations

if __name__ == "__main__":
    lex = Deepl()
    lex.translate('monster','nl','fr')
    # lex.search('before','en')
    # lex.search_list('angle,armoire,banc,bureau,cabinet,carreau,chaise,classe,clé,coin,couloir,dossier,eau','fr')
    # lex.search_list('against,pattern,slow,center,love,person,money,serve,appear,road,map,rain,rule,govern','en')
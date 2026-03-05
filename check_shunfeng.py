import urllib.request
import json
import urllib.parse
from config import MAP_API
import sqlite3

TK = MAP_API['tianditu']['key']

def search(word):
    url = f"http://api.tianditu.gov.cn/geocoder?ds={urllib.parse.quote(json.dumps({'keyWord': word}))}&tk={TK}"
    resp = urllib.request.urlopen(url).read().decode('utf-8')
    data = json.loads(resp)
    print(word, '->', data.get('location'))

search('江西省上饶市弋阳县曹溪镇')
search('江西省上饶市弋阳县曹溪镇邵畈')
search('江西省上饶市弋阳县曹溪镇东山')
search('弋阳县顺风加油站')

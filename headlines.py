from flask import Flask
from flask import render_template
from flask import request
from flask import make_response
import datetime
import feedparser
import json
import urllib3

app = Flask(__name__)

DEFAULTS = {'publication':'bbc',
            'city':'London,UK',
            'currency_from':'GBP',
            'currency_to':'USD'
            }

RSS_FEEDS = {'bbc':"http://feeds.bbci.co.uk/news/rss.xml",
             'cnn':'http://rss.cnn.com/rss/edition.rss',
             'fox':'http://feeds.foxnews.com/foxnews/latest',
             'iol':'http://www.iol.co.za/cmlink/1.640'}

CURRENCY_URL = "http://api.fixer.io/latest"

def get_rate(frm, to):
    http = urllib3.PoolManager()                        # urllib3 format
    all_currency = http.request('GET',CURRENCY_URL)     # urllib3 format
    all_currency = all_currency.data.decode('utf-8')    # needs the .decode(utf-8)
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate/frm_rate, parsed.keys())

@app.route('/terminal')
def terminal():
    http = urllib3.PoolManager()
    all_currency = http.request('GET',CURRENCY_URL)
    all_currency = all_currency.data.decode('utf-8')
    parsed = json.loads(all_currency).get('rates')
    rate = parsed['AUD']
    rate = str(rate)
    return rate

def get_weather(query): # page 110
    http = urllib3.PoolManager()
    api_url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=cb932829eacb6a0e9ee4f38bfbf112ed'
    # query = urllib.quote(query)
    # url = api_url.format(query)
    data = http.request('GET',api_url)
    # data = urllib.urlopen(url).read()
    parsed = json.loads(data.decode('utf-8'))
    weather = None
    if parsed.get("weather"):
        weather = {"description":parsed["weather"][0]["description"],
                   "temperature":parsed["main"]["temp"],
                   "city":parsed["name"]
                   }
        return weather

# @app.route('/<publication>') # <> defines variable
def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS["publication"]
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    # first_article = feed['entries'][10]
    return feed['entries']

def get_weather(query):
    pass
    # page 115

def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]

@app.route('/')
def home():
    # get customized headlines, based on user input or default
    publication = get_value_with_fallback("publication")
    articles = get_news(publication)

    # get customized weather based on our input or default
    city = get_value_with_fallback("city")
    # weather = get_weather(city)

    # get customized currency based on our input or default
    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies = get_rate(currency_from,currency_to)

    # save cookies and return template
    response = make_response(render_template("home.html",
                                             articles=articles,
                                             currency_from=currency_from,
                                             currency_to=currency_to,
                                             rate=rate,
                                             currencies=sorted(currencies))) # ,weather=weather
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("publication",publication,expires=expires)
    response.set_cookie("city",city,expires=expires)
    response.set_cookie("currency_from",currency_from,expires=expires)
    response.set_cookie("currency_to", currency_to, expires=expires)
    return response


if __name__ == '__main__':
    app.run(port=5000, debug=True)
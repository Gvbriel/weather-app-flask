from flask import Flask, redirect, url_for, render_template, request
from pytz import timezone
from datetime import datetime, timedelta
import re
from geopy.geocoders import Nominatim
from tzwhere import tzwhere
import pycountry_convert as pc

import pyowm
import configparser
import pytz
import requests 
import json
import sys

app = Flask(__name__)

def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['openweathermap']['api']

api_key = get_api_key()
owm = pyowm.OWM(api_key)
wthmgr = owm.weather_manager()
geolocator = Nominatim(user_agent='gvbplk')


def setImage(Weather):
    status = Weather.info[0]
    time = Weather.time
    
    if time < 6 or time > 21:
        if re.search("night", status) or re.search("sky", status):
            return 'https://svgshare.com/i/U2C.svg'
        elif re.search("few clouds", status) or re.search("clouds", status):
            return 'https://svgshare.com/i/U21.svg'
    elif time >= 6 and time <= 21:
        if re.search("clouds", status):
            return 'https://svgshare.com/i/U2D.svg'
        elif re.search("few clouds", status) or re.search("scattered clouds", status):
            return 'https://svgshare.com/i/U2d.svg'
        elif re.search("sun", status) or re.search("sky", status):
            return 'https://svgshare.com/i/U1X.svg'
        elif re.search("haze", status) or re.search("mist", status) or re.search("smoke", status):
            return 'https://svgshare.com/i/U04.svg'
        elif re.search("light rain", status):
            return "https://svgshare.com/i/U0b.svg"
        elif re.search("rain", status) or re.search("moderate rain", status):
            return "https://svgshare.com/i/U34.svg"
        elif re.search("snow", status):
            return "https://svgshare.com/i/U0a.svg"
        else:
            return 'https://svgshare.com/i/U1X.svg'
    
def continentName(Weather):
    countryalpha = pc.country_name_to_country_alpha2(Weather.country, cn_name_format="default")
    countrycode = pc.country_alpha2_to_continent_code(countryalpha)
    continent = pc.convert_continent_code_to_continent_name(countrycode)
    return str(continent)

def checkUS(continent):
    if "America" in continent:
        return "America"
    else:
        return continent


#add hour in the city
class Weather:
    
    def __init__(self, city, country):
        self.info = []
        self.city = str(city)
        self.country = str(country)
        self.place = wthmgr.weather_at_place(self.city + ', ' + self.country)
        
        self.info.append(str(self.place.weather.detailed_status))
        self.info.append(int(round(self.place.weather.temperature('celsius')['temp'],1)))
        self.info.append(round(self.place.weather.wind('km_hour')['speed'],2))
        
        self.latitude = geolocator.geocode(self.city + ','+ self.country).latitude
        self.longitude = geolocator.geocode(self.city + ','+ self.country).longitude
        self.continent = continentName(self)
        self.continent = checkUS(self.continent)
        self.citySpace = self.city.replace(' ', '_')
        self.timezone = self.continent + '/' + self.citySpace
        self.zone = pytz.timezone(self.timezone)
        self.time = int(datetime.now(self.zone).hour)
        self.image = str(setImage(self))
        
   
Lublin = wthmgr.weather_at_place('Lublin')
pogoda = Lublin.weather

Warsaw = Weather('Warsaw', 'Poland')
Tokyo = Weather('Tokyo', 'Japan')
Amsterdam = Weather('Amsterdam', 'Netherlands')
Shanghai = Weather('Shanghai', 'China')
SaoPaulo = Weather('Sao Paulo', 'Brazil')
NewYork = Weather('New York', 'United States')
BuenosAires = Weather('Buenos Aires', 'Argentina')
LosAngeles = Weather('Los Angeles', 'United States')
Paris = Weather('Paris', 'France')
Bangkok = Weather('Bangkok', 'Thailand')
Madrid = Weather('Madrid', 'Spain')
Manila = Weather('Manila', 'Philippines')
Moscow = Weather('Moscow', 'Russia')

citieslist = [Warsaw, Amsterdam, Tokyo, Shanghai, NewYork, BuenosAires, LosAngeles, Paris, Bangkok, Madrid, Manila, Moscow]

@app.route('/index.html')
def index():
    print(pogoda, file = sys.stderr)
    return render_template("index.html", cities = citieslist)

@app.route('/search.html', methods = ["POST","GET"])
def search():
    if request.method == "POST":
        cityInput = request.form["cityname"]
        countryInput = request.form["countryname"]
        cityInput = str(cityInput)
        countryInput = str(countryInput)
        cityInfo = Weather(cityInput, countryInput)
        print(cityInfo, file = sys.stderr)
        return render_template("search.html", display = True, city = cityInfo)
    else:
        return render_template("search.html", display = False, city = Warsaw)

@app.route('/<city>')
def city():
    return render_template("city.html")

if __name__ == "__main__":
    app.run(debug=True)
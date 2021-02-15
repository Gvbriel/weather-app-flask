from flask import Flask, redirect, url_for, render_template, request
from pytz import timezone
from datetime import datetime, timedelta
from re import search
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
    basepath = 'icons/'
    status = Weather.info[0]
    time = Weather.time
    
    if time < 6 or time > 21:
        if search("night", status) or search("sky", status):
            return basepath + 'night.svg'
        elif search("few clouds", status) or search("clouds", status):
            return basepath + 'cloudy-night-1.svg'
    elif time >= 6 and time <= 21:
        if search("clouds", status):
            return basepath + 'cloudy.svg'
        elif search("few clouds", status) or search("scattered clouds", status):
            return basepath + 'small-clouds.svg'
        elif search("sun", status) or search("sky", status):
            return basepath + 'day.svg'
        elif search("haze", status) or search("mist", status) or search("smoke", status):
            return basepath + 'haze.svg'
        elif search("light rain", status):
            return basepath + "rain.svg"
        elif search("rain", status) or search("moderate rain", status):
            return basepath + "raining.svg"
        elif search("snow", status):
            return basepath + "snowylight-day.svg"
        else:
            return basepath + 'sun.svg'
    
def continentName(Weather):
    countryalpha = pc.country_name_to_country_alpha2(Weather.country, cn_name_format="default")
    countrycode = pc.country_alpha2_to_continent_code(countryalpha)
    continent = pc.convert_continent_code_to_continent_name(countrycode)
    return str(continent)

def checkUS(Weather):
    if search("America", Weather.continent):
        return "America"
    else:
        return Weather.continent


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
        self.continent = checkUS(self)
        self.citySpace = self.city.replace(' ', '_')
        self.timezone = self.continent + '/' + self.citySpace
        self.zone = pytz.timezone(self.timezone)
        self.time = int(datetime.now(self.zone).hour)
        self.image = str(setImage(self))
        
   

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

@app.route('/')
def index():
    #print(NewYork.time, file = sys.stderr)
    return render_template("index.html", cities = citieslist)

@app.route('/search.html', methods=['POST'])
def search():
    if request.method == "POST":
        cityInput = request.form["cityname"]
        countryInput = request.form["countryname"]
        cityInput = str(cityInput)
        countryInput = str(countryInput)
        cityInfo = Weather(cityInput, countryInput)
        #print(cityInfo, file = sys.stderr)
        return render_template("search.html", display = True, city = cityInfo)
    else:
        return render_template("search.html", display = False, city = "Warsaw")

if __name__ == "__main__":
    app.run(debug=True)
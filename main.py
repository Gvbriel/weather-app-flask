from flask import Flask, redirect, url_for, render_template, request, Response
from pytz import timezone
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from tzwhere import tzwhere
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from matplotlib.figure import Figure
import matplotlib
import io
from base64 import b64encode
import base64

import pycountry_convert as pc
import re
import pyowm
import configparser
import pytz
import requests 
import json
import sys

app = Flask(__name__)

#set backend to non-interactive one; without it I get error about not running matplotlib in main thread
matplotlib.use('agg')

#get api key from ini file
def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['openweathermap']['api']

api_key = get_api_key()
owm = pyowm.OWM(api_key)
wthmgr = owm.weather_manager()
geolocator = Nominatim(user_agent='gvbplk')


def setImage(Weather):
    status = str(Weather.status)
    time = Weather.time
    
    if time < 6 or time > 21:
        if re.search("night", status) or re.search("sky", status):
            return 'https://svgshare.com/i/U2C.svg'
        elif re.search("few clouds", status) or re.search("clouds", status):
            return 'https://svgshare.com/i/U21.svg'
        elif re.search("rain" , status):
            return 'https://svgshare.com/i/U34.svg'
        elif re.search("mist" , status) or re.search("haze" , status) or re.search("smoke", status):
            return 'https://svgshare.com/i/U5G.svg'
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

def createPlot(Weather):
    tempMax = Weather.forecastTempMax
    tempMin = Weather.forecastTempMin
    dates = Weather.forecastDates

    plt.plot(tempMax, dates, label="Max day temperature")
    plt.plot(tempMin, dates, label="Min day temperature")
    plt.ylabel('Temperature')
    plt.xlabel('Dates')
    plt.title('7 days forecast')

    plt.savefig(Weather.city + '.png')


class WeatherAtCity:
    def __init__(self, city):
        self.city = city
        self.place = wthmgr.weather_at_place(self.city)
        self.status = self.place.weather.detailed_status
        self.temp = int(round(self.place.weather.temperature('celsius')['temp'],1))
        self.wind = round(self.place.weather.wind('km_hour')['speed'],2)
        self.image = setImage(self)



class Weather:
    
    def __init__(self, city, country):
        self.forecastTempMax = []
        self.forecastTempMin = []
        self.forecastDates = []
        self.city = city
        self.country = country
        self.place = wthmgr.weather_at_place(self.city + ', ' + self.country)

        self.status = self.place.weather.detailed_status
        self.temp = int(round(self.place.weather.temperature('celsius')['temp'],1))
        self.wind = round(self.place.weather.wind('km_hour')['speed'],2)
        self.pressure = self.place.weather.pressure['press']
        self.sunrise = self.place.weather.sunrise_time(timeformat="date")
        self.sunset = self.place.weather.sunset_time(timeformat="date")
        self.tempDif = self.place.weather.temperature('celsius')
        self.tempMax = round(self.tempDif['temp_max'],1)
        self.tempMin = round(self.tempDif['temp_min'],1)
       
        
        self.lat = geolocator.geocode(self.city + ','+ self.country).latitude
        self.long = geolocator.geocode(self.city + ','+ self.country).longitude

        self.dailyForecaster = wthmgr.forecast_at_place(self.city + ', ' + self.country, '3h')
        self.oneCallForecast = wthmgr.one_call(self.lat, self.long).forecast_daily
        self.continent = continentName(self)
        self.continent = checkUS(self.continent)
        self.citySpace = self.city.replace(' ', '_')
        self.timezone = self.continent + '/' + self.citySpace
        self.zone = pytz.timezone(self.timezone)
        self.time = int(datetime.now(self.zone).hour)
        self.image = setImage(self)
        self.sunrise = self.sunrise.replace(tzinfo=pytz.utc).astimezone(self.zone)
        self.sunset = self.sunset.replace(tzinfo=pytz.utc).astimezone(self.zone)

        self.coldest = self.dailyForecaster.most_cold()
        self.hottest = self.dailyForecaster.most_hot()
        self.rainest = self.dailyForecaster.most_rainy()
        self.snowy = self.dailyForecaster.most_snowy()
        

        self.longTermForecast()

    def longTermForecast(self):
        for weather in self.oneCallForecast:
            self.forecastTempMax.append(round(float(weather.temperature('celsius').get('max')),1))
            self.forecastTempMin.append(round(float(weather.temperature('celsius').get('min')),1))
            day = datetime.utcfromtimestamp(weather.reference_time())
            date = day.date()
            self.forecastDates.append(date.strftime("%m-%d"))



Warsaw = Weather('Warsaw', 'Poland')
Tokyo = Weather('Tokyo', 'Japan')
Amsterdam = Weather('Amsterdam', 'Netherlands')
Shanghai = Weather('Shanghai', 'China')
NewYork = Weather('New York', 'United States')
BuenosAires = Weather('Buenos Aires', 'Argentina')
LosAngeles = Weather('Los Angeles', 'United States')
Paris = Weather('Paris', 'France')
Bangkok = Weather('Bangkok', 'Thailand')
Madrid = Weather('Madrid', 'Spain')
Manila = Weather('Manila', 'Philippines')
Moscow = Weather('Moscow', 'Russia')

citieslist = [Warsaw, Amsterdam, NewYork, Tokyo, Shanghai, BuenosAires, LosAngeles, Paris, Bangkok, Madrid, Manila, Moscow]

@app.route('/index.html')
def index():
    print(Warsaw.coldest, file = sys.stderr)
    print(Warsaw.rainest, file = sys.stderr)
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

@app.route('/city.html')
def city():
    cityC = request.args.get('city')
    countryC = request.args.get('country')
    city = Weather(cityC, countryC)

    tempMax = city.forecastTempMax
    tempMin = city.forecastTempMin
    dates = city.forecastDates

    img = io.BytesIO()

    plt.clf()
    #plt.xkcd()
    plt.plot(dates, tempMax, color='#1f77b4',marker='.', label="Highest temperature")
    plt.plot(dates, tempMin, color='#17becf',marker='.', label="Lowest temperature")
    plt.ylabel('Temperature (Celsius)')
    plt.xlabel('Dates')
    plt.title('7 days forecast')
    plt.legend()

    plt.grid(b=True, linestyle='dashed')

    axes = plt.gca()
    axes.set_ylim([min(tempMin)-5, max(tempMax)+5])

    for i,j in zip(dates,tempMin):
        axes.annotate(str(j),xy=(i,j), xytext=(-13,-15), textcoords='offset points')

    for i,j in zip(dates,tempMax):
        axes.annotate(str(j),xy=(i,j), xytext=(-13,10), textcoords='offset points')

    plt.savefig(img, format='png')
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()

    print(city, file = sys.stderr)
    return render_template("city.html", city = city, url = plot_url)

if __name__ == "__main__":
    app.run(debug=True)
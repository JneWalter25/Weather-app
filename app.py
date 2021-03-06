import requests
import sys
from datetime import datetime, timezone, timedelta, time
from os import path
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, flash, redirect,url_for

db = SQLAlchemy()
DB_NAME = "weather.db"


class Cities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))


def create_database(app_):
    if not path.exists('web/' + DB_NAME):
        db.create_all(app=app_)
        print('Created Database!')


def create_app():
    app_ = (Flask(__name__))
    app_.config['SECRET_KEY'] = 'slBnLfa70xYt'
    app_.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app_.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app_)

    create_database(app_)

    return app_


app = create_app()


def get_part_of_day(utc_offset):
    utc_now = datetime.now(timezone.utc)
    current_time = (utc_now + timedelta(seconds=utc_offset)).time()
    night_time = time(hour=20)
    evening_morning_time = time(hour=8)

    if night_time > current_time > evening_morning_time:
        return 'day'
    elif night_time < current_time < evening_morning_time:
        return 'night'
    else:
        return 'evening-morning'


def get_weather_arr(api_):
    all_city = Cities.query.all()
    weather_arr_ = []
    for city_ in all_city:
        r = requests.get('http://api.openweathermap.org/data/2.5/weather',
                         params={'appid': api_, 'q': city_.name, 'units': 'metric', 'lang': 'en'})
        data = r.json()
        if 'name' in data:
            city_name = data['name']
            part_of_day = get_part_of_day(data['timezone'])
            state = data['weather'][0]['main']
            temperature = data['main']['temp']
            dict_with_weather_info = {
                'city_name': city_name,
                'state': state,
                'temperature': temperature,
                'part_of_day': part_of_day
            }
            weather_arr_.append(dict_with_weather_info)

        else:
            flash("The city doesn't exist!", 'danger')
    return weather_arr_


@app.route('/', methods=['POST', 'GET'])
def weather():
    api = '210baf44b65389fcbd24dadadb20c308'
    if request.method == 'POST':
                weather_arr = get_weather_arr(api)
                city = request.form['city_name']
                result = Cities.query.filter_by(name=city).first()
                if not result:
                    new_city = Cities(name=city)
                    db.session.add(new_city)
                    db.session.commit()
                else:
                    flash("The city has already been added to the list!", 'danger')
                weather_arr = get_weather_arr(api)
                return render_template('city.html', weather=weather_arr)
    else:
        weather_arr = get_weather_arr(api)
        return render_template('city.html', weather=weather_arr)



@app.route('/delete/', methods=['GET', 'POST'])
def delete():
    city = Cities.query.first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')

# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port, debug=True)
    else:
        app.run(debug=True)
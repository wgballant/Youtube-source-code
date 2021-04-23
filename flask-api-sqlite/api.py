import datetime
import json
import uuid

from datetime import *
from flask import Flask, make_response, jsonify, request
import dataset


app = Flask(__name__)
db = dataset.connect('sqlite:///restaurants.db')
table = db['restaurants']


@app.route('/api/restaurants', methods=['GET', 'POST'])
def api_restaurants():
    if request.method == "GET":
        return make_response(jsonify(fetch_db_all()), 200)
    elif request.method == 'POST':
        content = request.json
        hours = content.get('hours')
        name = content.get('name')
        if not name or not hours:
            return make_response(jsonify({}), 400)
        valid_hours, normalized_hours = validate_hours(hours)
        if valid_hours:
            content['hours'] = normalized_hours
            restaurant_id = str(uuid.uuid1())
            content['restaurant_id'] = restaurant_id
            table.insert(content)
            return make_response(jsonify(fetch_db(restaurant_id)), 201)  # 201 = Created
        return make_response(jsonify({}), 400)


@app.route('/api/restaurants/<restaurant_id>', methods=['GET', 'PUT', 'DELETE'])
def api_each_restaurant(restaurant_id):

    if request.method == "GET":
        restaurant_obj = fetch_db(restaurant_id)
        if restaurant_obj:
            restaurant_obj['is_open'] = restaurant_open(restaurant_obj['Hours'])
            return make_response(jsonify(restaurant_obj), 200)
        else:
            return make_response(jsonify(restaurant_obj), 404)
    elif request.method == "PUT":  # Updates the restaurant
        content = request.json
        content['restaurant_id'] = restaurant_id
        updated_hours = content.get('Hours')
        updated_name = content.get('name')
        if updated_name:
            content['name'] = updated_name
        valid_hours, normalized_hours = validate_hours(updated_hours)
        if valid_hours:
            content['Hours'] = normalized_hours
        table.update(content, ['restaurant_id'])
        restaurant_obj = fetch_db(restaurant_id)
        return make_response(jsonify(restaurant_obj), 200)
    elif request.method == "DELETE":
        table.delete(restaurant_id=restaurant_id)
        return make_response(jsonify({}), 204)


@app.route('/api/db_populate', methods=['GET'])
def db_populate():
    table.insert({
        "restaurant_id": str(uuid.uuid1()),
        "name": "The Chowdown",
        "hours": {
            "Friday": {
                "open": "19:00",
                "close": "22:00"
            },
            "Saturday": {
                "open": "19:00",
                "close": "22:00"
            }
        }
    })

    table.insert({
        "restaurant_id": str(uuid.uuid1()),
        "name": "Bobs Burgers",
        "hours": {
            "Friday": {
                "open": "19:00",
                "close": "22:00"
            },
            "Saturday": {
                "open": "16:00",
                "close": "23:00"
            }
        }
    })

    return make_response(jsonify(fetch_db_all()),
                         200)


@app.route('/api/db_depopulate', methods=['GET'])
def db_depopulate():
    table.delete()
    return make_response(jsonify(fetch_db_all()),
                         200)


def validate_hours(hours):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if not hours:
        return False
    hours_dict = json.loads(hours)
    out_hours = {}
    for key, value in hours_dict.items():
        if key not in days:
            return False

        open_str = value.get('open')
        close_str = value.get('close')
        if not (open_str and close_str):
            return False
        open_time = datetime.strptime(open_str, "%I:%M%p")
        close_time = datetime.strptime(close_str, "%I:%M%p")
        if open_time > close_time:
            return False
        open_time_24h = datetime.strftime(open_time, "%H:%M")
        close_time_24h = datetime.strftime(close_time, "%H:%M")
        out_hours[key] = {'open': open_time_24h, 'close': close_time_24h}

    return True, out_hours


def restaurant_open(hours):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    now = datetime.now()
    day = days[datetime.weekday(now)]
    hours_today = hours.get(day)
    if not hours_today:
        return False
    now = now.replace(year=1900, month=1, day=1)
    open_obj = datetime.strptime(hours_today['open'], "%H:%M")
    close_obj = datetime.strptime(hours_today['close'], "%H:%M")
    if open_obj < now < close_obj:
        return True
    return False


def fetch_db(restaurant_id):
    return table.find_one(restaurant_id=restaurant_id)


def fetch_db_all():
    restaurants = []
    for restaurant in table:
        restaurants.append(restaurant)
    return restaurants


if __name__ == '__main__':
    app.run(debug=True)

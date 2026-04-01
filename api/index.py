from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/weather')
def get_weather():
    city = request.args.get('city')
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url).json()
        if not geo_res.get('results'): return jsonify({"error": "City not found"}), 404
        
        loc = geo_res['results'][0]
        lat, lon = loc['latitude'], loc['longitude']

        # 2. Advanced Weather Fetch (Current + Hourly + Daily)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current_weather=true&hourly=temperature_2m,weathercode&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&timezone=auto"
        )
        data = requests.get(weather_url).json()

        # Format Hourly (next 24 hours)
        hourly_list = []
        for i in range(24):
            hourly_list.append({
                "time": data['hourly']['time'][i].split("T")[1],
                "temp": data['hourly']['temperature_2m'][i],
                "code": data['hourly']['weathercode'][i]
            })

        return jsonify({
            "city": loc['name'],
            "temp": data['current_weather']['temperature'],
            "wind": data['current_weather']['windspeed'],
            "hourly": hourly_list,
            "daily_max": data['daily']['temperature_2m_max'],
            "daily_min": data['daily']['temperature_2m_min']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
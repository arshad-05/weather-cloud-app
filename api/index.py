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

        # 2. Comprehensive Fetch (Current + Daily + Hourly + Air Quality)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max"
            f"&hourly=temperature_2m&timezone=auto&forecast_days=7"
        )
        data = requests.get(weather_url).json()

        # Format 7-Day Forecast
        daily_list = []
        for i in range(7):
            daily_list.append({
                "date": data['daily']['time'][i],
                "max": data['daily']['temperature_2m_max'][i],
                "min": data['daily']['temperature_2m_min'][i],
                "code": data['daily']['weather_code'][i]
            })

        return jsonify({
            "city": loc['name'],
            "country": loc.get('country', ''),
            "current": data['current'],
            "daily": daily_list,
            "hourly_temp": data['hourly']['temperature_2m'][:24] # Next 24 hours
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
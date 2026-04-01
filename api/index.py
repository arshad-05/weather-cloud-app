from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

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

        # 2. Fetch data (Current + Hourly + Daily)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max"
            f"&hourly=temperature_2m&timezone=auto"
        )
        data = requests.get(weather_url).json()

        # 3. GET CURRENT HOUR TO SLICE DATA
        current_hour = datetime.now().hour
        
        # Get temperatures starting from the current hour for the next 24 hours
        all_hourly_temps = data['hourly']['temperature_2m']
        # Slice from current hour to current hour + 24
        sliced_temps = all_hourly_temps[current_hour : current_hour + 24]
        
        # Create a labeled list for the frontend
        hourly_forecast = []
        for i, temp in enumerate(sliced_temps):
            hour_label = (current_hour + i) % 24
            hourly_forecast.append({
                "time": f"{hour_label}:00",
                "temp": temp
            })

        # Format Daily
        daily_list = []
        for i in range(7):
            daily_list.append({
                "date": data['daily']['time'][i],
                "max": data['daily']['temperature_2m_max'][i],
                "min": data['daily']['temperature_2m_min'][i]
            })

        return jsonify({
            "city": loc['name'],
            "current": data['current'],
            "daily": daily_list,
            "hourly_data": hourly_forecast  # Send the sliced data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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

        # 2. Fetch data with timezone auto-detection
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m,time"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
            f"&hourly=temperature_2m,weather_code&timezone=auto"
        )
        data = requests.get(weather_url).json()

        # 3. Find "Now" in the Hourly Array
        current_time_str = data['current']['time'] # Format: "2026-04-01T12:00"
        hourly_times = data['hourly']['time']
        
        # Find the index where hourly time matches current time
        start_index = hourly_times.index(current_time_str) if current_time_str in hourly_times else 0
        
        # Slice next 24 hours starting from "Now"
        next_24_temps = data['hourly']['temperature_2m'][start_index : start_index + 24]
        next_24_times = data['hourly']['time'][start_index : start_index + 24]

        hourly_forecast = []
        for i in range(len(next_24_temps)):
            # Format time to show "12:00" or "Now"
            time_label = "Now" if i == 0 else next_24_times[i].split("T")[1]
            hourly_forecast.append({
                "time": time_label,
                "temp": next_24_temps[i]
            })

        return jsonify({
            "city": loc['name'],
            "local_time": current_time_str.replace("T", " "),
            "current": data['current'],
            "daily": data['daily'],
            "hourly_data": hourly_forecast
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url).json()
        if not geo_res.get('results'): return jsonify({"error": "City not found"}), 404
        
        loc = geo_res['results'][0]
        lat, lon = loc['latitude'], loc['longitude']

        # Ensure "current" is in the parameters string
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,surface_pressure,wind_speed_10m,time"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&hourly=temperature_2m&timezone=auto"
        )
        data = requests.get(weather_url).json()

        # Find "Now" for the hourly slice
        current_time_str = data['current']['time']
        hourly_times = data['hourly']['time']
        start_index = hourly_times.index(current_time_str) if current_time_str in hourly_times else 0
        
        next_24_temps = data['hourly']['temperature_2m'][start_index : start_index + 24]
        next_24_times = data['hourly']['time'][start_index : start_index + 24]

        hourly_forecast = []
        for i in range(len(next_24_temps)):
            time_label = "Now" if i == 0 else next_24_times[i].split("T")[1]
            hourly_forecast.append({"time": time_label, "temp": next_24_temps[i]})

        # THE CRITICAL PART: The keys here must match the frontend
        return jsonify({
            "city": loc['name'],
            "local_time": current_time_str.replace("T", " "),
            "current": data['current'], # This MUST exist
            "daily": data['daily'],
            "hourly_data": hourly_forecast
        })
    except Exception as e:
        # This is why you saw the alert('current') — it caught an error named 'current'
        return jsonify({"error": str(e)}), 500
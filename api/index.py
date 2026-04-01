from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app) # Allows your HTML file to talk to this Python API

@app.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "No city provided"}), 400

    try:
        # 1. Geocoding API: Get Lat/Lon from City Name
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_data = requests.get(geo_url).json()
        
        if 'results' not in geo_data:
            return jsonify({"error": "City not found"}), 404
        
        location = geo_data['results'][0]
        lat, lon = location['latitude'], location['longitude']

        # 2. Weather API: Get Current Weather + Air Quality (AQI)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=pm2_5,uv_index"
        weather_res = requests.get(weather_url).json()

        return jsonify({
            "city": location['name'],
            "country": location.get('country', ''),
            "temp": weather_res['current_weather']['temperature'],
            "condition_code": weather_res['current_weather']['weathercode'],
            "wind": weather_res['current_weather']['windspeed']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel
def handler(event, context):
    return app(event, context)
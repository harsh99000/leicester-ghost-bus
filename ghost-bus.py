import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, send_file

app = Flask(__name__)

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js')

API_KEY = os.environ.get('BODS_API_KEY')
URL = f"https://data.bus-data.dft.gov.uk/api/v1/datafeed?api_key={API_KEY}&operatorRef=AMID&lineRef=48"

def get_bus_data():
    response = requests.get(URL)
    root = ET.fromstring(response.content)
    now = datetime.now(timezone.utc)
    bus_list = []

    for activity in root.findall(".//{*}VehicleActivity"):
        journey = activity.find(".//{*}MonitoredVehicleJourney")
        recorded_at = activity.findtext("{*}RecordedAtTime")
        
        bus_time = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
        diff = (now - bus_time).total_seconds() / 60
        
        bus_list.append({
            "id": journey.findtext("{*}VehicleRef"),
            "lat": float(journey.findtext(".//{*}Latitude")),
            "lon": float(journey.findtext(".//{*}Longitude")),
            "status": "LIVE" if diff < 5 else "GHOST",
            "delay": round(diff, 1)
        })
    return bus_list

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/buses')
def api_buses():
    return jsonify(get_bus_data())

if __name__ == "__main__":
    # use_reloader=False stops Spyder from crashing
    app.run(debug=True, use_reloader=False)
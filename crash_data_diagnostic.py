import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import radians, cos, sin, asin, sqrt
import webbrowser
import os
from datetime import datetime

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r * 1000  # Return distance in meters

def load_crash_data(api_url=None, file_path=None):
    """
    Load crash data from either an API URL or a local file.
    """
    data = None
    
    if api_url:
        try:
            print(f"Fetching crash data from API: {api_url}")
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            print(f"Successfully fetched {len(data)} crash records!")
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from API: {e}")
            # If API fails, we'll try the file path if provided
    
    if file_path:
        try:
            print(f"Loading crash data from file: {file_path}")
            with open(file_path, 'r') as file:
                data = json.load(file)
            print(f"Successfully loaded {len(data)} crash records!")
            return data
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
        except json.JSONDecodeError:
            print(f"Error: File '{file_path}' does not contain valid JSON.")
    
    return data

def load_citibike_data(file_path):
    """
    Load Citi Bike station data from a file.
    """
    try:
        print(f"Loading Citi Bike data from: {file_path}")
        with open(file_path, 'r') as file:
            stations = json.load(file)
        print(f"Successfully loaded {len(stations)} Citi Bike stations!")
        return stations
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' does not contain valid JSON.")
        return None

def clean_crash_data(crashes):
    """
    Clean and prepare crash data for analysis.
    """
    print("Cleaning crash data...")
    
    # First, let's inspect the data structure
    if isinstance(crashes, list):
        print(f"Data is a list with {len(crashes)} items")
        df = pd.DataFrame(crashes)
    elif isinstance(crashes, dict):
        print("Data is a dictionary with keys:", list(crashes.keys()))
        
        # Handle various API response formats
        if 'data' in crashes:
            df = pd.DataFrame(crashes['data'])
        # Handle NYC Open Data API format
        elif any(key in crashes for key in ['columns', 'rows']):
            print("Detected NYC Open Data API format")
            if 'rows' in crashes and isinstance(crashes['rows'], list):
                print(f"Found {len(crashes['rows'])} rows")
                
                # Get column names if available
                column_names = None
                if 'columns' in crashes and isinstance(crashes['columns'], list):
                    try:
                        column_names = [col['name'] for col in crashes['columns']]
                        print(f"Found column names: {column_names}")
                    except (KeyError, TypeError):
                        print("Could not extract column names from 'columns' field")
                
                # Convert rows to DataFrame
                df = pd.DataFrame(crashes['rows'], columns=column_names)
            else:
                print("Error: Could not find usable data rows")
                return pd.DataFrame()
        else:
            print("Error: Unexpected crash data format")
            print("Keys found:", list(crashes.keys()))
            return pd.DataFrame()
    else:
        print(f"Error: Unexpected data type: {type(crashes)}")
        return pd.DataFrame()
    
    # Check for expected columns and rename if needed
    column_mapping = {
        'crash_date': 'date',
        'crash_time': 'time',
        'latitude': 'lat',
        'longitude': 'lon',
        'number_of_cyclist_injured': 'cyclists_injured',
        'number_of_cyclist_killed': 'cyclists_killed',
        'borough': 'borough',
        'zip_code': 'zip',
        'on_street_name': 'street',
        'cross_street_name': 'cross_street',
        'contributing_factor_vehicle_1': 'factor1'
    }
    
    # Rename columns that exist in the DataFrame
    rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    # Print column names to help debug
    print("Available columns in dataset:")
    for col in df.columns:
        print(f"  - {col}")
    
    # Ensure required columns exist
    required_columns = ['lat', 'lon', 'cyclists_injured', 'cyclists_killed']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: Missing required columns: {missing_columns}")
        # Try to infer missing columns
        if 'latitude' in df.columns and 'lat' not in df.columns:
            print("Mapping 'latitude' to 'lat'")
            df['lat'] = df['latitude']
        if 'longitude' in df.columns and 'lon' not in df.columns:
            print("Mapping 'longitude' to 'lon'")
            df['lon'] = df['longitude']
        if 'number_of_cyclist_injured' in df.columns and 'cyclists_injured' not in df.columns:
            print("Mapping 'number_of_cyclist_injured' to 'cyclists_injured'")
            df['cyclists_injured'] = df['number_of_cyclist_injured']
        if 'number_of_cyclist_killed' in df.columns and 'cyclists_killed' not in df.columns:
            print("Mapping 'number_of_cyclist_killed' to 'cyclists_killed'")
            df['cyclists_killed'] = df['number_of_cyclist_killed']
            
    # Check again for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"ERROR: Still missing required columns after inference: {missing_columns}")
        print("Sample data from first row:")
        if len(df) > 0:
            print(df.iloc[0].to_dict())
    
    # Convert numeric columns first
    for col in ['lat', 'lon', 'cyclists_injured', 'cyclists_killed']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Then filter for incidents with cyclists
    df = df[(df['cyclists_injured'] > 0) | (df['cyclists_killed'] > 0)]
    
    # Drop rows with missing lat/lon
    df = df.dropna(subset=['lat', 'lon'])
    
    # Add total cyclist casualties column
    df['total_cyclist_casualties'] = df['cyclists_injured'] + df['cyclists_killed']
    
    # Convert date and time if available
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
        except:
            print("Warning: Could not parse crash dates")
    
    print(f"Cleaned data contains {len(df)} cyclist-involved crashes")
    return df

def analyze_crash_data(crashes_df):
    """
    Analyze crash data to extract insights.
    """
    print("\n===== BIKE CRASH ANALYSIS =====")
    print(f"Total crashes involving cyclists: {len(crashes_df)}")
    
    total_injured = crashes_df['cyclists_injured'].sum()
    total_killed = crashes_df['cyclists_killed'].sum()
    
    print(f"Total cyclists injured: {total_injured}")
    print(f"Total cyclists killed: {total_killed}")
    print(f"Total casualties: {total_injured + total_killed}")
    
    # Month and time analysis if available
    if 'date' in crashes_df.columns:
        crashes_df['month'] = crashes_df['date'].dt.month
        month_counts = crashes_df.groupby('month').size()
        print("\nCrashes by month:")
        for month, count in month_counts.items():
            month_name = datetime(2024, month, 1).strftime('%B')
            print(f"{month_name}: {count} crashes")
    
    # Borough analysis if available
    if 'borough' in crashes_df.columns:
        borough_counts = crashes_df['borough'].value_counts()
        print("\nCrashes by borough:")
        for borough, count in borough_counts.items():
            if pd.notna(borough) and borough:
                print(f"{borough}: {count} crashes")
    
    # Contributing factors analysis if available
    if 'factor1' in crashes_df.columns:
        factor_counts = crashes_df['factor1'].value_counts().head(5)
        print("\nTop 5 contributing factors:")
        for factor, count in factor_counts.items():
            if pd.notna(factor) and factor:
                print(f"{factor}: {count} crashes")

def analyze_proximity(crashes_df, stations):
    """
    Analyze the proximity of crashes to Citi Bike stations.
    """
    print("\n===== PROXIMITY ANALYSIS =====")
    
    # Filter stations with valid coordinates
    valid_stations = [
        s for s in stations 
        if 'lat' in s and 'lon' in s and 
        isinstance(s['lat'], (int, float)) and 
        isinstance(s['lon'], (int, float))
    ]
    
    if not valid_stations:
        print("No valid station coordinates for proximity analysis.")
        return
    
    # Calculate distance from each crash to nearest station
    distances = []
    for _, crash in crashes_df.iterrows():
        closest_distance = float('inf')
        for station in valid_stations:
            distance = haversine(crash['lon'], crash['lat'], station['lon'], station['lat'])
            if distance < closest_distance:
                closest_distance = distance
        distances.append(closest_distance)
    
    crashes_df['distance_to_nearest_station'] = distances
    
    # Analyze the distances
    avg_distance = crashes_df['distance_to_nearest_station'].mean()
    median_distance = crashes_df['distance_to_nearest_station'].median()
    
    print(f"Average distance from crash to nearest Citi Bike station: {avg_distance:.1f} meters")
    print(f"Median distance from crash to nearest Citi Bike station: {median_distance:.1f} meters")
    
    # Count crashes within different radii of stations
    within_100m = (crashes_df['distance_to_nearest_station'] <= 100).sum()
    within_250m = (crashes_df['distance_to_nearest_station'] <= 250).sum()
    within_500m = (crashes_df['distance_to_nearest_station'] <= 500).sum()
    
    print(f"Crashes within 100m of a station: {within_100m} ({within_100m/len(crashes_df)*100:.1f}%)")
    print(f"Crashes within 250m of a station: {within_250m} ({within_250m/len(crashes_df)*100:.1f}%)")
    print(f"Crashes within 500m of a station: {within_500m} ({within_500m/len(crashes_df)*100:.1f}%)")
    
    return crashes_df

def plot_crash_data(crashes_df, stations):
    """
    Create a visualization of crash data.
    """
    # Filter stations with valid coordinates
    valid_stations = [
        s for s in stations 
        if 'lat' in s and 'lon' in s and 
        isinstance(s['lat'], (int, float)) and 
        isinstance(s['lon'], (int, float))
    ]
    
    # Extract coordinates
    station_lats = [station['lat'] for station in valid_stations]
    station_lons = [station['lon'] for station in valid_stations]
    
    # Create the plot
    plt.figure(figsize=(12, 10))
    
    # Plot crashes with color based on severity
    severity = crashes_df['total_cyclist_casualties']
    plt.scatter(crashes_df['lon'], crashes_df['lat'], 
                c=severity, cmap='YlOrRd', alpha=0.7, 
                s=severity*20+20, edgecolors='black', linewidths=0.5)
    
    # Plot station locations
    plt.scatter(station_lons, station_lats, 
                c='blue', alpha=0.3, s=10, 
                marker='s', label='Citi Bike Station')
    
    plt.title('Bike Crashes and Citi Bike Stations (2024)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add colorbar for crash severity
    cbar = plt.colorbar()
    cbar.set_label('Cyclist Casualties')
    
    # Save the plot
    plt.savefig('bike_crashes_map.png')
    print("Map saved as 'bike_crashes_map.png'")
    plt.show()

def create_interactive_map(crashes_df, stations):
    """
    Create an interactive HTML map showing crashes and stations.
    """
    print("Creating interactive map...")
    
    # Filter stations with valid coordinates
    valid_stations = [
        s for s in stations 
        if 'lat' in s and 'lon' in s and 
        isinstance(s['lat'], (int, float)) and 
        isinstance(s['lon'], (int, float))
    ]
    
    # Create simplified datasets for the map
    station_data = []
    for station in valid_stations:
        station_data.append({
            "name": station.get('name', 'Unknown Station'),
            "lat": station['lat'],
            "lon": station['lon'],
            "id": station.get('station_id', 'Unknown'),
            "capacity": station.get('capacity', 0),
            "type": "station"
        })
    
    crash_data = []
    for _, crash in crashes_df.iterrows():
        crash_info = {
            "lat": crash['lat'],
            "lon": crash['lon'],
            "injured": int(crash['cyclists_injured']),
            "killed": int(crash['cyclists_killed']),
            "total": int(crash['total_cyclist_casualties']),
            "type": "crash"
        }
        
        # Add optional fields if they exist
        for field in ['date', 'time', 'borough', 'street', 'cross_street', 'factor1', 'distance_to_nearest_station']:
            if field in crash and pd.notna(crash[field]):
                crash_info[field] = crash[field]
        
        crash_data.append(crash_info)
    
    # Create the HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bike Safety Analysis: Crashes and Citi Bike Stations</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            #map { height: 80vh; width: 100%; }
            .header { padding: 10px; background-color: #f5f5f5; border-bottom: 1px solid #ddd; }
            .info-panel {
                padding: 6px 8px;
                font: 14px/16px Arial, sans-serif;
                background: white;
                background: rgba(255,255,255,0.8);
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;
            }
            .info-panel h4 { margin: 0 0 5px; color: #777; }
            .legend { line-height: 18px; color: #555; }
            .legend i {
                width: 18px;
                height: 18px;
                float: left;
                margin-right: 8px;
                opacity: 0.7;
            }
            .controls {
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            #charts { 
                display: flex; 
                flex-wrap: wrap; 
                justify-content: space-around; 
                margin-top: 20px;
            }
            .chart-container {
                width: 45%;
                min-width: 300px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Bike Safety Analysis: 2024 Crashes and Citi Bike Stations</h1>
            <p>Visualization of cyclist crashes and their proximity to Citi Bike stations in NYC</p>
        </div>
        
        <div id="map"></div>
        
        <div id="charts">
            <div class="chart-container">
                <canvas id="proximityChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="severityChart"></canvas>
            </div>
        </div>
        
        <script>
            // Map initialization
            var map = L.map('map').setView([40.75, -73.98], 12);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
            
            // Load data
            var stations = """
    
    # Add station data
    html_content += json.dumps(station_data)
    
    html_content += """;
            
            var crashes = """
    
    # Add crash data
    html_content += json.dumps(crash_data)
    
    html_content += """;
            
            // Calculate distance between points using Haversine formula
            function haversineDistance(lat1, lon1, lat2, lon2) {
                function toRad(x) {
                    return x * Math.PI / 180;
                }
                
                var R = 6371; // km
                var dLat = toRad(lat2-lat1);
                var dLon = toRad(lon2-lon1);
                var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * 
                        Math.sin(dLon/2) * Math.sin(dLon/2);
                var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                var d = R * c;
                return d * 1000; // Convert to meters
            }
            
            // Calculate distance from each crash to nearest station if not already calculated
            crashes.forEach(function(crash) {
                if (!crash.distance_to_nearest_station) {
                    var minDist = Infinity;
                    stations.forEach(function(station) {
                        var dist = haversineDistance(
                            crash.lat, crash.lon,
                            station.lat, station.lon
                        );
                        if (dist < minDist) {
                            minDist = dist;
                        }
                    });
                    crash.distance_to_nearest_station = minDist;
                }
            });
            
            // Add station markers
            stations.forEach(function(station) {
                var marker = L.circleMarker([station.lat, station.lon], {
                    radius: 4,
                    fillColor: '#3388ff',
                    color: '#3388ff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.6
                }).addTo(map);
                
                marker.bindPopup(`
                    <b>${station.name}</b><br>
                    Station ID: ${station.id}<br>
                    Capacity: ${station.capacity}
                `);
            });
            
            // Add crash markers
            crashes.forEach(function(crash) {
                // Determine color based on severity
                var color = crash.killed > 0 ? '#ff0000' : (crash.total > 1 ? '#ff6600' : '#ffcc00');
                
                var marker = L.circleMarker([crash.lat, crash.lon], {
                    radius: 5 + (crash.total * 2),
                    fillColor: color,
                    color: '#000',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.8
                }).addTo(map);
                
                var popupContent = `
                    <b>Cyclist Crash</b><br>
                    Cyclists Injured: ${crash.injured}<br>
                    Cyclists Killed: ${crash.killed}<br>
                `;
                
                if (crash.date) popupContent += `Date: ${crash.date}<br>`;
                if (crash.time) popupContent += `Time: ${crash.time}<br>`;
                if (crash.borough) popupContent += `Borough: ${crash.borough}<br>`;
                if (crash.street) popupContent += `Location: ${crash.street}`;
                if (crash.cross_street) popupContent += ` & ${crash.cross_street}`;
                popupContent += `<br>`;
                if (crash.factor1) popupContent += `Contributing Factor: ${crash.factor1}<br>`;
                popupContent += `Distance to nearest Citi Bike station: ${crash.distance_to_nearest_station.toFixed(0)} meters`;
                
                marker.bindPopup(popupContent);
            });
            
            // Add a legend
            var legend = L.control({position: 'bottomright'});
            legend.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'info-panel legend');
                div.innerHTML = `
                    <h4>Crash Severity</h4>
                    <i style="background:#ff0000"></i> Fatal crash<br>
                    <i style="background:#ff6600"></i> Multiple injuries<br>
                    <i style="background:#ffcc00"></i> Single injury<br>
                    <i style="background:#3388ff"></i> Citi Bike station
                `;
                return div;
            };
            legend.addTo(map);
            
            // Add info panel with statistics
            var info = L.control({position: 'topright'});
            info.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'info-panel');
                
                // Calculate statistics
                var totalCrashes = crashes.length;
                var totalInjured = crashes.reduce((sum, c) => sum + c.injured, 0);
                var totalKilled = crashes.reduce((sum, c) => sum + c.killed, 0);
                
                var within100m = crashes.filter(c => c.distance_to_nearest_station <= 100).length;
                var within250m = crashes.filter(c => c.distance_to_nearest_station <= 250).length;
                var within500m = crashes.filter(c => c.distance_to_nearest_station <= 500).length;
                
                div.innerHTML = `
                    <h4>Crash Statistics (2024)</h4>
                    <p><strong>Total Crashes:</strong> ${totalCrashes}</p>
                    <p><strong>Cyclists Injured:</strong> ${totalInjured}</p>
                    <p><strong>Cyclists Killed:</strong> ${totalKilled}</p>
                    <p><strong>Crashes within 250m of a station:</strong> ${within250m} (${(within250m/totalCrashes*100).toFixed(1)}%)</p>
                `;
                return div;
            };
            info.addTo(map);
            
            // Create charts
            document.addEventListener('DOMContentLoaded', function() {
                // Proximity chart
                var proximityCounts = [
                    crashes.filter(c => c.distance_to_nearest_station <= 100).length,
                    crashes.filter(c => c.distance_to_nearest_station > 100 && c.distance_to_nearest_station <= 250).length,
                    crashes.filter(c => c.distance_to_nearest_station > 250 && c.distance_to_nearest_station <= 500).length,
                    crashes.filter(c => c.distance_to_nearest_station > 500).length
                ];
                
                var proximityCtx = document.getElementById('proximityChart').getContext('2d');
                var proximityChart = new Chart(proximityCtx, {
                    type: 'bar',
                    data: {
                        labels: ['≤ 100m', '101-250m', '251-500m', '> 500m'],
                        datasets: [{
                            label: 'Crashes by Distance to Nearest Station',
                            data: proximityCounts,
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.7)',
                                'rgba(255, 159, 64, 0.7)',
                                'rgba(255, 205, 86, 0.7)',
                                'rgba(75, 192, 192, 0.7)'
                            ],
                            borderColor: [
                                'rgb(255, 99, 132)',
                                'rgb(255, 159, 64)',
                                'rgb(255, 205, 86)',
                                'rgb(75, 192, 192)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Crashes by Distance to Nearest Citi Bike Station'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Number of Crashes'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Distance'
                                }
                            }
                        }
                    }
                });
                
                // Severity chart
                var severityCounts = [
                    crashes.filter(c => c.injured == 1 && c.killed == 0).length,
                    crashes.filter(c => c.injured > 1 && c.killed == 0).length,
                    crashes.filter(c => c.killed > 0).length
                ];
                
                var severityCtx = document.getElementById('severityChart').getContext('2d');
                var severityChart = new Chart(severityCtx, {
                    type: 'pie',
                    data: {
                        labels: ['Single Injury', 'Multiple Injuries', 'Fatal'],
                        datasets: [{
                            label: 'Crash Severity',
                            data: severityCounts,
                            backgroundColor: [
                                'rgba(255, 205, 86, 0.7)',
                                'rgba(255, 159, 64, 0.7)',
                                'rgba(255, 99, 132, 0.7)'
                            ],
                            borderColor: [
                                'rgb(255, 205, 86)',
                                'rgb(255, 159, 64)',
                                'rgb(255, 99, 132)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Crash Severity Distribution'
                            },
                            legend: {
                                position: 'right'
                            }
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    # Write the HTML to a file
    with open('bike_safety_map.html', 'w') as f:
        f.write(html_content)
    
    # Open the HTML file in the default web browser
    print("Interactive map created as 'bike_safety_map.html'")
    webbrowser.open('file://' + os.path.realpath('bike_safety_map.html'))

def main():
    print("==============================")
    print("Bike Safety Analysis Tool")
    print("==============================")
    
    # First, load the crash data
    print("\nSTEP 1: Load Crash Data")
    print("------------------------")
    source_choice = input("Load crash data from (1) API or (2) local file? Enter 1 or 2: ")
    
    crash_data = None
    if source_choice == '1':
        api_url = input("Enter the crash data API URL: ")
        crash_data = load_crash_data(api_url=api_url)
        
        # Option to save the data
        if crash_data:
            save_option = input("Would you like to save this data locally for future use? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename (default: crash_data_2024.json): ") or "crash_data_2024.json"
                with open(filename, 'w') as f:
                    json.dump(crash_data, f)
                print(f"Data saved to {filename}")
    else:
        file_path = input("Enter the path to the crash data file: ")
        crash_data = load_crash_data(file_path=file_path)
    
    if not crash_data:
        print("Failed to load crash data. Exiting program.")
        return
    
    # Clean and prepare the crash data
    crashes_df = clean_crash_data(crash_data)
    
    if len(crashes_df) == 0:
        print("No valid crash data after cleaning. Exiting program.")
        return
    
    # Now load the Citi Bike station data
    print("\nSTEP 2: Load Citi Bike Station Data")
    print("-----------------------------------")
    citibike_file = input("Enter the path to the Citi Bike station data file (or press enter for default 'citibike_combined_data.json'): ")
    
    if not citibike_file:
        citibike_file = "citibike_combined_data.json"
    
    stations = load_citibike_data(citibike_file)
    
    if not stations:
        print("Failed to load station data. Exiting program.")
        return
    
    # Main menu
    while True:
        print("\nBike Safety Analysis Menu")
        print("=========================")
        print("1. Analyze crash data")
        print("2. Analyze proximity to Citi Bike stations")
        print("3. Create static visualization")
        print("4. Create interactive map")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            analyze_crash_data(crashes_df)
        elif choice == '2':
            crashes_df = analyze_proximity(crashes_df, stations)
        elif choice == '3':
            plot_crash_data(crashes_df, stations)
        elif choice == '4':
            create_interactive_map(crashes_df, stations)
        elif choice == '5':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()

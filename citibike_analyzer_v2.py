import json
import matplotlib.pyplot as plt
import webbrowser
import os

def load_combined_data(file_path):
    """
    Load station data from a combined JSON file.
    """
    try:
        print(f"Loading data from: {file_path}")
        with open(file_path, 'r') as file:
            stations = json.load(file)
        print(f"Successfully loaded {len(stations)} stations.")
        return stations
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' does not contain valid JSON.")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def analyze_stations(stations):
    """
    Perform basic analysis on the station data.
    """
    total_stations = len(stations)
    active_stations = sum(1 for s in stations if s.get('is_installed', 1) == 1)
    total_capacity = sum(s.get('capacity', 0) for s in stations)
    total_bikes = sum(s.get('num_bikes_available', 0) for s in stations)
    total_ebikes = sum(s.get('num_ebikes_available', 0) for s in stations)
    total_docks = sum(s.get('num_docks_available', 0) for s in stations)
    
    print("\n===== CITI BIKE NETWORK ANALYSIS =====")
    print(f"Total stations: {total_stations}")
    print(f"Active stations: {active_stations}")
    print(f"Total bike capacity: {total_capacity}")
    print(f"Regular bikes available: {total_bikes - total_ebikes}")
    print(f"E-bikes available: {total_ebikes}")
    print(f"Total bikes available: {total_bikes}")
    print(f"Total docks available: {total_docks}")
    
    # Calculate the average station size
    if active_stations > 0:
        avg_capacity = total_capacity / active_stations
        print(f"\nAverage station capacity: {avg_capacity:.1f} bikes")
    
    # Find stations with most and least available bikes
    active_stations_list = [s for s in stations if s.get('is_installed', 1) == 1 and s.get('is_renting', 1) == 1]
    if active_stations_list:
        most_bikes = max(active_stations_list, key=lambda x: x.get('num_bikes_available', 0))
        least_bikes = min(active_stations_list, key=lambda x: x.get('num_bikes_available', 0))
        
        print(f"\nStation with most bikes: {most_bikes.get('name', 'Unknown')} ({most_bikes.get('num_bikes_available', 0)} bikes)")
        print(f"Station with least bikes: {least_bikes.get('name', 'Unknown')} ({least_bikes.get('num_bikes_available', 0)} bikes)")
        
        # Find stations with highest and lowest utilization
        for station in active_stations_list:
            capacity = station.get('capacity', 0)
            if capacity > 0:
                station['utilization'] = station.get('num_bikes_available', 0) / capacity
            else:
                station['utilization'] = 0
        
        most_utilized = max(active_stations_list, key=lambda x: x.get('utilization', 0))
        least_utilized = min(active_stations_list, key=lambda x: x.get('utilization', 0))
        
        print(f"\nMost utilized station: {most_utilized.get('name', 'Unknown')} ({most_utilized.get('utilization', 0)*100:.1f}% full)")
        print(f"Least utilized station: {least_utilized.get('name', 'Unknown')} ({least_utilized.get('utilization', 0)*100:.1f}% full)")
    
    # Analyze station distribution by borough/region if available
    if any('region_id' in station for station in stations):
        regions = {}
        for station in stations:
            region_id = station.get('region_id', 'Unknown')
            if region_id not in regions:
                regions[region_id] = 0
            regions[region_id] += 1
        
        print("\nStations by region ID:")
        for region_id, count in sorted(regions.items(), key=lambda x: x[1], reverse=True):
            print(f"Region {region_id}: {count} stations")

def plot_stations(stations):
    """
    Create a basic plot of station locations.
    """
    # Filter to only installed stations with valid coordinates
    valid_stations = [
        s for s in stations 
        if s.get('is_installed', 1) == 1 and 
        'lat' in s and 'lon' in s and 
        isinstance(s['lat'], (int, float)) and 
        isinstance(s['lon'], (int, float))
    ]
    
    if not valid_stations:
        print("No valid stations to plot.")
        return
    
    print(f"Plotting {len(valid_stations)} stations with valid coordinates...")
    
    # Create color mapping based on available bikes
    colors = []
    sizes = []
    
    for station in valid_stations:
        # Color based on utilization (bikes/capacity)
        capacity = station.get('capacity', 0)
        bikes = station.get('num_bikes_available', 0)
        
        if capacity > 0:
            utilization = bikes / capacity
        else:
            utilization = 0
        
        # Green for full, red for empty, yellow for in between
        if utilization > 0.7:
            colors.append('green')
        elif utilization < 0.3:
            colors.append('red')
        else:
            colors.append('orange')
            
        # Size based on capacity
        sizes.append(max(20, station.get('capacity', 10) / 2))
    
    # Extract coordinates
    lats = [station['lat'] for station in valid_stations]
    lons = [station['lon'] for station in valid_stations]
    
    # Create the plot
    plt.figure(figsize=(12, 10))
    plt.scatter(lons, lats, c=colors, s=sizes, alpha=0.7)
    
    plt.title('Citi Bike Station Locations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    
    # Add a legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='High availability (>70%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='Medium availability (30-70%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Low availability (<30%)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    # Save the plot as an image
    plt.savefig('citibike_stations_map.png')
    print("Map saved as 'citibike_stations_map.png'")
    plt.show()

def create_interactive_map(stations):
    """
    Create an interactive HTML map of the stations.
    """
    # Filter to only installed stations with valid coordinates
    valid_stations = [
        s for s in stations 
        if 'lat' in s and 'lon' in s and 
        isinstance(s['lat'], (int, float)) and 
        isinstance(s['lon'], (int, float))
    ]
    
    if not valid_stations:
        print("No valid stations to display on the map.")
        return
    
    print(f"Creating interactive map with {len(valid_stations)} stations...")
    
    # Create a simplified dataset for the map
    map_data = []
    for station in valid_stations:
        capacity = station.get('capacity', 0)
        bikes_available = station.get('num_bikes_available', 0)
        is_active = station.get('is_installed', 1) == 1 and station.get('is_renting', 1) == 1
        
        # Calculate utilization for color
        if capacity > 0:
            utilization = bikes_available / capacity
        else:
            utilization = 0
            
        # Determine status color
        if not is_active:
            status_color = "gray"  # Inactive station
        elif utilization > 0.7:
            status_color = "green"  # High availability
        elif utilization < 0.3:
            status_color = "red"    # Low availability
        else:
            status_color = "orange" # Medium availability
        
        map_data.append({
            "name": station.get('name', 'Unknown Station'),
            "lat": station['lat'],
            "lon": station['lon'],
            "id": station.get('station_id', 'Unknown'),
            "bikes": bikes_available,
            "ebikes": station.get('num_ebikes_available', 0),
            "docks": station.get('num_docks_available', 0),
            "capacity": capacity,
            "status": "Active" if is_active else "Inactive",
            "color": status_color
        })
    
    # Create the HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Citi Bike Stations</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            body { margin: 0; padding: 0; }
            #map { height: 100vh; width: 100%; }
            .info-panel {
                padding: 6px 8px;
                font: 14px/16px Arial, Helvetica, sans-serif;
                background: white;
                background: rgba(255,255,255,0.8);
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;
            }
            .info-panel h4 {
                margin: 0 0 5px;
                color: #777;
            }
            .legend {
                line-height: 18px;
                color: #555;
            }
            .legend i {
                width: 18px;
                height: 18px;
                float: left;
                margin-right: 8px;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Map initialization
            var map = L.map('map').setView([40.75, -73.98], 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
            
            // Station data
            var stations = """
    
    # Add the JSON data to the HTML
    html_content += json.dumps(map_data)
    
    # Continue with the rest of the HTML
    html_content += """
            
            // Add markers for each station
            stations.forEach(function(station) {
                var circleMarker = L.circleMarker([station.lat, station.lon], {
                    radius: Math.min(12, Math.max(5, station.capacity / 5)),
                    fillColor: station.color,
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);
                
                // Create popup content
                var popupContent = `
                    <div style="min-width: 200px;">
                        <h3>${station.name}</h3>
                        <p><strong>Status:</strong> ${station.status}</p>
                        <p><strong>Regular Bikes:</strong> ${station.bikes - station.ebikes}</p>
                        <p><strong>E-Bikes:</strong> ${station.ebikes}</p>
                        <p><strong>Docks Available:</strong> ${station.docks}</p>
                        <p><strong>Capacity:</strong> ${station.capacity}</p>
                        <p><strong>Station ID:</strong> ${station.id}</p>
                    </div>
                `;
                
                circleMarker.bindPopup(popupContent);
            });
            
            // Add a legend
            var legend = L.control({position: 'bottomright'});
            legend.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'info-panel legend');
                div.innerHTML = `
                    <h4>Station Status</h4>
                    <i style="background:green"></i> High Availability<br>
                    <i style="background:orange"></i> Medium Availability<br>
                    <i style="background:red"></i> Low Availability<br>
                    <i style="background:gray"></i> Inactive Station
                `;
                return div;
            };
            legend.addTo(map);
            
            // Add info panel with statistics
            var info = L.control({position: 'topright'});
            info.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'info-panel');
                div.innerHTML = `
                    <h4>Citi Bike Network</h4>
                    <p><strong>Total Stations:</strong> ${stations.length}</p>
                    <p><strong>Active Stations:</strong> ${stations.filter(s => s.status === 'Active').length}</p>
                    <p><strong>Total Bikes Available:</strong> ${stations.reduce((sum, s) => sum + s.bikes, 0)}</p>
                    <p><strong>E-Bikes Available:</strong> ${stations.reduce((sum, s) => sum + s.ebikes, 0)}</p>
                `;
                return div;
            };
            info.addTo(map);
        </script>
    </body>
    </html>
    """
    
    # Write the HTML to a file
    with open('citibike_map.html', 'w') as f:
        f.write(html_content)
    
    # Open the HTML file in the default web browser
    print("Interactive map created as 'citibike_map.html'")
    webbrowser.open('file://' + os.path.realpath('citibike_map.html'))

def main():
    print("==========================")
    print("Citi Bike Station Analyzer")
    print("==========================")
    
    # Ask for the combined data file
    print("\nThis program works with the combined Citi Bike data that includes both")
    print("station information (locations) and status (available bikes/docks).")
    
    file_path = input("\nEnter the path to the combined data JSON file (or press enter for default 'citibike_combined_data.json'): ")
    
    if not file_path:
        file_path = "citibike_combined_data.json"
    
    # Load the station data
    stations = load_combined_data(file_path)
    
    if not stations:
        print("Failed to load station data. Exiting program.")
        return
    
    # Main menu
    while True:
        print("\nCiti Bike Station Analyzer Menu")
        print("===============================")
        print("1. Show network analysis")
        print("2. Plot station locations (static map)")
        print("3. Create interactive map (opens in browser)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            analyze_stations(stations)
        elif choice == '2':
            plot_stations(stations)
        elif choice == '3':
            create_interactive_map(stations)
        elif choice == '4':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()

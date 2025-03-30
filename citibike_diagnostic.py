import requests
import json

def inspect_api_data(url):
    """
    Fetch and analyze the structure of data from an API URL.
    """
    print(f"Fetching data from: {url}")
    
    try:
        # Get the data from the API
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Print the top-level structure
        print("\n--- Top-level structure ---")
        for key in data:
            if isinstance(data[key], dict):
                print(f"{key}: <dictionary with {len(data[key])} keys>")
            elif isinstance(data[key], list):
                print(f"{key}: <list with {len(data[key])} items>")
            else:
                print(f"{key}: {data[key]}")
        
        # If 'data' exists, investigate its structure
        if 'data' in data and isinstance(data['data'], dict):
            print("\n--- Structure of 'data' field ---")
            for key in data['data']:
                if isinstance(data['data'][key], dict):
                    print(f"{key}: <dictionary with {len(data['data'][key])} keys>")
                elif isinstance(data['data'][key], list):
                    print(f"{key}: <list with {len(data['data'][key])} items>")
                else:
                    print(f"{key}: {data['data'][key]}")
            
            # If 'stations' exists inside 'data', look at a sample station
            if 'stations' in data['data'] and isinstance(data['data']['stations'], list) and len(data['data']['stations']) > 0:
                sample_station = data['data']['stations'][0]
                print("\n--- Sample station fields ---")
                for key in sample_station:
                    print(f"{key}: {sample_station[key]}")
        
        # Check if we have a list of stations directly
        elif isinstance(data, list) and len(data) > 0:
            sample_item = data[0]
            print("\n--- Sample item fields ---")
            for key in sample_item:
                print(f"{key}: {sample_item[key]}")
        
        # Try to count stations and other key data points
        station_count = 0
        if 'data' in data and 'stations' in data['data']:
            station_count = len(data['data']['stations'])
        
        print(f"\nDetected approximately {station_count} stations.")
        print("\nNOTE: The station_status.json endpoint provides current status (bikes available, etc.)")
        print("To get station locations, you should use station_information.json instead.")
        
        # Try to combine both datasets if the user wants
        combine_data = input("\nWould you like to try fetching station information as well? (y/n): ")
        if combine_data.lower() == 'y':
            info_url = "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
            print(f"\nFetching station information from: {info_url}")
            
            try:
                info_response = requests.get(info_url)
                info_response.raise_for_status()
                info_data = info_response.json()
                
                if 'data' in info_data and 'stations' in info_data['data']:
                    info_stations = info_data['data']['stations']
                    print(f"Found {len(info_stations)} stations in the information endpoint.")
                    
                    if len(info_stations) > 0:
                        sample_info = info_stations[0]
                        print("\n--- Sample station information ---")
                        for key in sample_info:
                            print(f"{key}: {sample_info[key]}")
                    
                    # Create a combined dataset
                    print("\nCreating a combined dataset with both information and status...")
                    
                    # Create a dictionary of station IDs to station information
                    station_info_dict = {station['station_id']: station for station in info_stations}
                    
                    # Get status data
                    status_stations = []
                    if 'data' in data and 'stations' in data['data']:
                        status_stations = data['data']['stations']
                    
                    # Combine the datasets
                    combined_stations = []
                    for status in status_stations:
                        station_id = status.get('station_id')
                        if station_id and station_id in station_info_dict:
                            # Merge the dictionaries
                            combined = {**station_info_dict[station_id], **status}
                            combined_stations.append(combined)
                    
                    print(f"Created a combined dataset with {len(combined_stations)} stations.")
                    
                    # Save to file option
                    save_option = input("Would you like to save this combined dataset to a file? (y/n): ")
                    if save_option.lower() == 'y':
                        filename = "citibike_combined_data.json"
                        with open(filename, 'w') as f:
                            json.dump(combined_stations, f, indent=2)
                        print(f"Data saved to {filename}")
                        
                        # Provide snippet of code to load this data
                        print("\nUse this code to load the saved data in your program:")
                        print("```python")
                        print("import json")
                        print("with open('citibike_combined_data.json', 'r') as f:")
                        print("    stations = json.load(f)")
                        print("print(f'Loaded {len(stations)} stations')")
                        print("```")
            
            except Exception as e:
                print(f"Error fetching station information: {e}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = input("Enter the Citi Bike API URL (or press enter for default): ")
    if not url:
        url = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
    
    inspect_api_data(url)

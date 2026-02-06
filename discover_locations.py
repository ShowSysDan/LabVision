"""
ArtsVision Location Discovery Script
Gets ALL locations from your ArtsVision system
"""

import requests
import json
import urllib3
from datetime import datetime, timedelta

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = "823264392764"  # Replace with your actual API key
API_BASE_URL = "https://av2.artsvision.net/api"

print("=" * 80)
print("ArtsVision Location Discovery Tool")
print("=" * 80)
print()

# Method 1: Check if there's a Location entity
print("METHOD 1: Checking for Location entity...")
print("-" * 80)
try:
    response = requests.get(
        f"{API_BASE_URL}/getentitynames",
        headers={"apikey": API_KEY},
        timeout=30,
        verify=False
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('Status') == 0:
            entities = data.get('Data', [])
            location_entities = [e for e in entities if 'location' in e.lower()]
            
            if location_entities:
                print(f"✓ Found location entities: {location_entities}")
                
                # Try to get locations from the Location entity
                for entity_name in location_entities:
                    print(f"\nQuerying {entity_name}...")
                    
                    payload = {
                        "xml": False,
                        "flatten": False,
                        "entities": [
                            {
                                "entity": entity_name,
                                "firstRowIndex": 0,
                                "rowsCount": 500,
                                "columns": [],
                                "filters": [],
                                "orderby": [],
                                "include": []
                            }
                        ]
                    }
                    
                    loc_response = requests.post(
                        f"{API_BASE_URL}/getdata",
                        json=payload,
                        headers={"apikey": API_KEY, "Content-Type": "application/json"},
                        timeout=30,
                        verify=False
                    )
                    
                    if loc_response.status_code == 200:
                        loc_data = loc_response.json()
                        if loc_data.get('Status') == 0:
                            entities_data = loc_data.get('Data', [])
                            if entities_data and len(entities_data) > 0:
                                rows = entities_data[0].get('Rows', [])
                                print(f"  Found {len(rows)} location records")
                                
                                if rows:
                                    print(f"\n  Sample location data:")
                                    for key, value in rows[0].get('Data', {}).items():
                                        print(f"    {key}: {value}")
            else:
                print("✗ No Location entity found")
except Exception as e:
    print(f"ERROR: {e}")

print()
print()

# Method 2: Get events from a wide date range
print("METHOD 2: Getting events from extended date range...")
print("-" * 80)

# Try different date ranges
date_ranges = [
    (7, "Next 7 days"),
    (30, "Next 30 days"),
    (90, "Next 90 days"),
    (365, "Next year")
]

all_locations = set()

for days, label in date_ranges:
    print(f"\n{label}:")
    
    today = datetime.now().strftime("%m/%d/%Y")
    future = (datetime.now() + timedelta(days=days)).strftime("%m/%d/%Y")
    
    payload = {
        "xml": False,
        "flatten": False,
        "entities": [
            {
                "entity": "Event",
                "firstRowIndex": 0,
                "rowsCount": 500,
                "columns": ["Location"],  # Only get Location field
                "filters": [
                    {
                        "field": "Date",
                        "operator": "GreaterOrEqual",
                        "value": today
                    },
                    {
                        "field": "Date",
                        "operator": "Less",
                        "value": future
                    }
                ],
                "orderby": [],
                "include": []
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/getdata",
            json=payload,
            headers={"apikey": API_KEY, "Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('Status') == 0:
                entities = data.get('Data', [])
                if entities and len(entities) > 0:
                    rows = entities[0].get('Rows', [])
                    
                    locations = set()
                    for row in rows:
                        event_data = row.get('Data', {})
                        location = event_data.get('Location', '')
                        if location:
                            locations.add(location)
                            all_locations.add(location)
                    
                    print(f"  Events: {len(rows)}")
                    print(f"  Locations: {len(locations)}")
                    print(f"  New locations found: {len(locations - (all_locations - locations))}")
    except Exception as e:
        print(f"  ERROR: {e}")

print()
print()

# Method 3: Get ALL events (no date filter)
print("METHOD 3: Getting ALL events (no date filter)...")
print("-" * 80)

payload = {
    "xml": False,
    "flatten": False,
    "entities": [
        {
            "entity": "Event",
            "firstRowIndex": 0,
            "rowsCount": 1000,  # Get up to 1000 events
            "columns": ["Location"],
            "filters": [],  # No filters!
            "orderby": [
                {
                    "field": "Date",
                    "descending": True
                }
            ],
            "include": []
        }
    ]
}

try:
    response = requests.post(
        f"{API_BASE_URL}/getdata",
        json=payload,
        headers={"apikey": API_KEY, "Content-Type": "application/json"},
        timeout=60,  # Longer timeout
        verify=False
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('Status') == 0:
            entities = data.get('Data', [])
            if entities and len(entities) > 0:
                entity = entities[0]
                total_count = entity.get('TotalCount')
                rows = entity.get('Rows', [])
                
                print(f"Total events in system: {total_count}")
                print(f"Retrieved: {len(rows)} events")
                
                locations_all = set()
                for row in rows:
                    event_data = row.get('Data', {})
                    location = event_data.get('Location', '')
                    if location:
                        locations_all.add(location)
                        all_locations.add(location)
                
                print(f"Unique locations: {len(locations_all)}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print()

# Summary
print("=" * 80)
print("SUMMARY - ALL DISCOVERED LOCATIONS")
print("=" * 80)
print(f"\nTotal unique locations: {len(all_locations)}")
print()

if all_locations:
    sorted_locations = sorted(all_locations)
    for i, loc in enumerate(sorted_locations, 1):
        print(f"{i:3d}. {loc}")
    
    # Save to file
    with open('discovered_locations.txt', 'w') as f:
        f.write("All Discovered Locations from ArtsVision\n")
        f.write("=" * 60 + "\n\n")
        for loc in sorted_locations:
            f.write(f"{loc}\n")
    
    print()
    print(f"✓ Saved to 'discovered_locations.txt'")
else:
    print("No locations found!")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

if len(all_locations) > 0:
    print("✓ Locations discovered successfully!")
    print()
    print("To get all these locations in your app:")
    print("1. Increase the date range in .env:")
    print("   LOCATION_DISCOVERY_DAYS=90")
    print()
    print("2. Or use persistent location cache (already implemented)")
    print()
    print("3. The app will accumulate locations over time")
else:
    print("No locations found. Possible reasons:")
    print("- No events in the system")
    print("- Location field has a different name")
    print("- API permissions issue")

print()

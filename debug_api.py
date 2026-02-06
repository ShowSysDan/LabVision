"""
ArtsVision API Debug Script
This script tests the API connection and shows detailed information about what's being returned
"""

import requests
import json
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = "823264392764"  # Replace with your actual API key
API_BASE_URL = "https://av2.artsvision.net/api"

print("=" * 80)
print("ArtsVision API Debug Tool")
print("=" * 80)
print()

# Test 1: Get Entity Names
print("TEST 1: Getting all entity names...")
print("-" * 80)
try:
    response = requests.get(
        f"{API_BASE_URL}/getentitynames",
        headers={"apikey": API_KEY},
        timeout=30,
        verify=False
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('Status')}")
        
        if data.get('Status') == 0:
            entities = data.get('Data', [])
            print(f"Found {len(entities)} entities")
            print(f"First 10 entities: {entities[:10]}")
        else:
            print(f"API Error: {data.get('Data')}")
    else:
        print(f"HTTP Error: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print()

# Test 2: Get Event Metadata
print("TEST 2: Getting Event entity metadata...")
print("-" * 80)
try:
    response = requests.get(
        f"{API_BASE_URL}/getmetadata?startWithEntity=Event&fieldsInfo=true",
        headers={"apikey": API_KEY},
        timeout=30,
        verify=False
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('Status')}")
        
        if data.get('Status') == 0:
            metadata = data.get('Data', [])
            if metadata and len(metadata) > 0:
                event_meta = metadata[0]
                fields = event_meta.get('Fields', [])
                print(f"Event entity has {len(fields)} fields")
                
                # Show all field names
                print("\nAll Event fields:")
                for i, field in enumerate(fields, 1):
                    print(f"  {i:3d}. {field['Name']:40s} ({field['Type']})")
                
                # Look for time and location fields
                print("\nTime-related fields:")
                time_fields = [f for f in fields if 'time' in f['Name'].lower() or 'date' in f['Name'].lower()]
                for field in time_fields:
                    print(f"  - {field['Name']} ({field['Type']})")
                
                print("\nLocation-related fields:")
                location_fields = [f for f in fields if 'location' in f['Name'].lower() or 'place' in f['Name'].lower()]
                for field in location_fields:
                    print(f"  - {field['Name']} ({field['Type']})")
        else:
            print(f"API Error: {data.get('Data')}")
    else:
        print(f"HTTP Error: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print()

# Test 3: Get Today's Events (with different date formats)
print("TEST 3: Getting today's events...")
print("-" * 80)

today = datetime.now()
tomorrow = today + timedelta(days=1)

# Try different date formats
date_formats = [
    (today.strftime("%m/%d/%Y"), tomorrow.strftime("%m/%d/%Y"), "MM/DD/YYYY"),
    (today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"), "YYYY-MM-DD"),
    (today.strftime("%d/%m/%Y"), tomorrow.strftime("%d/%m/%Y"), "DD/MM/YYYY"),
]

for today_str, tomorrow_str, format_name in date_formats:
    print(f"\nTrying date format: {format_name}")
    print(f"  Today: {today_str}")
    print(f"  Tomorrow: {tomorrow_str}")
    
    payload = {
        "xml": False,
        "flatten": False,
        "entities": [
            {
                "entity": "Event",
                "firstRowIndex": 0,
                "rowsCount": 50,
                "columns": [],
                "filters": [
                    {
                        "field": "Date",
                        "operator": "GreaterOrEqual",
                        "value": today_str
                    },
                    {
                        "field": "Date",
                        "operator": "Less",
                        "value": tomorrow_str
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
            headers={
                "apikey": API_KEY,
                "Content-Type": "application/json"
            },
            timeout=30,
            verify=False
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response Status: {data.get('Status')}")
            
            if data.get('Status') == 0:
                entities = data.get('Data', [])
                if entities and len(entities) > 0:
                    rows = entities[0].get('Rows', [])
                    print(f"  ✓ SUCCESS! Found {len(rows)} events")
                    
                    if rows and len(rows) > 0:
                        print(f"\n  First event data:")
                        first_event = rows[0].get('Data', {})
                        for key, value in first_event.items():
                            print(f"    {key}: {value}")
                        break  # Found data, stop trying other formats
                else:
                    print(f"  No data returned")
            else:
                print(f"  API Error: {data.get('Data')}")
        else:
            print(f"  HTTP Error")
    except Exception as e:
        print(f"  ERROR: {e}")

print()
print()

# Test 4: Get ALL events (no date filter) - limited to 10
print("TEST 4: Getting all events (no date filter, max 10)...")
print("-" * 80)

payload = {
    "xml": False,
    "flatten": False,
    "entities": [
        {
            "entity": "Event",
            "firstRowIndex": 0,
            "rowsCount": 10,
            "columns": [],
            "filters": [],
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
        headers={
            "apikey": API_KEY,
            "Content-Type": "application/json"
        },
        timeout=30,
        verify=False
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('Status')}")
        
        if data.get('Status') == 0:
            entities = data.get('Data', [])
            if entities and len(entities) > 0:
                entity = entities[0]
                total_count = entity.get('TotalCount')
                rows = entity.get('Rows', [])
                
                print(f"Total events in system: {total_count}")
                print(f"Retrieved: {len(rows)} events")
                
                if rows and len(rows) > 0:
                    print(f"\nMost recent event:")
                    recent_event = rows[0].get('Data', {})
                    
                    # Show all fields
                    print(f"\nAll fields in this event:")
                    for key, value in recent_event.items():
                        print(f"  {key:40s} = {value}")
                    
                    # Check for dates
                    print(f"\nDate-related fields:")
                    for key, value in recent_event.items():
                        if 'date' in key.lower() or 'time' in key.lower():
                            print(f"  {key}: {value}")
            else:
                print(f"No data returned")
        else:
            print(f"API Error: {data.get('Data')}")
    else:
        print(f"HTTP Error: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=" * 80)
print("Debug Complete!")
print("=" * 80)
print()
print("NEXT STEPS:")
print("1. Look for 'SUCCESS!' message - that shows the correct date format")
print("2. Check the field names in the event data")
print("3. Compare with what api_poller.py is looking for")
print("4. Update api_poller.py to use the correct field names")
# Location Discovery Guide

## Problem

You're only seeing locations that have events **today**. Many of your locations might not have events scheduled for today, so they don't appear in the dropdown.

## Solution

I've added **3 ways** to discover all locations:

---

## Method 1: Extended Date Range (Automatic)

The app now looks further into the future to find ALL locations.

### Configuration

Edit `.env`:

```ini
# Look 90 days ahead (default)
LOCATION_DISCOVERY_DAYS=90

# Or look a full year ahead
LOCATION_DISCOVERY_DAYS=365

# Or just one month
LOCATION_DISCOVERY_DAYS=30
```

### How It Works

**At startup:**
1. App queries events for next 90 days (or configured value)
2. Collects all locations from those events
3. Stores them in database

**During operation:**
- Continues to add new locations as it discovers them
- Locations accumulate over time
- Never removes locations (persistent)

### Benefits

✅ Automatic - no manual work needed
✅ Finds locations from future events  
✅ Configurable - adjust date range as needed
✅ Persistent - locations stay in dropdown

---

## Method 2: Location Entity (If Available)

The app also tries to query a dedicated "Location" entity if one exists in your ArtsVision system.

### What It Does

**At startup:**
1. Checks if there's a "Location" entity
2. If found, queries all location records
3. Adds them to the dropdown

### Check Logs

```
Discovering all locations...
Found location entities: ['Location']
  Location: Found 47 location records
Total locations discovered: 47
```

### If No Location Entity

```
Discovering all locations...
No Location entity found
Found 1000 events in next 90 days
Discovered 15 unique locations from events
```

---

## Method 3: Manual Discovery Script

I've created a script that shows you ALL locations in your system.

### Run the Script

1. **Activate virtual environment:**
   ```cmd
   cd "E:\OneDrive - Dr. Phillips Performing Arts Center\Python\artsvision-monitor"
   venv\Scripts\activate.bat
   ```

2. **Download discover_locations.py** (from files above)

3. **Run it:**
   ```cmd
   python discover_locations.py
   ```

### What It Shows

```
================================================================================
ArtsVision Location Discovery Tool
================================================================================

METHOD 1: Checking for Location entity...
Found location entities: ['Location']
...

METHOD 2: Getting events from extended date range...
Next 7 days: 45 events, 8 locations
Next 30 days: 123 events, 12 locations
Next 90 days: 287 events, 15 locations
...

METHOD 3: Getting ALL events (no date filter)...
Total events in system: 2,847
Retrieved: 1000 events
Unique locations: 18

================================================================================
SUMMARY - ALL DISCOVERED LOCATIONS
================================================================================

Total unique locations: 18

  1. Alexis & Jim Pugh Theater
  2. Dock A
  3. Dock B
  4. HP Field House
  5. Margeson Theater
  6. Steinmetz Hall
  7. ...

✓ Saved to 'discovered_locations.txt'
```

---

## Quick Fix Right Now

### Option 1: Increase Date Range

Edit `.env`:
```ini
LOCATION_DISCOVERY_DAYS=365
```

Restart:
```cmd
Ctrl+C
run.bat
```

Watch logs:
```
Discovering all locations...
Found 287 events in next 365 days
Discovered 25 unique locations from events
Location discovery complete: 25 locations available
```

### Option 2: Run Discovery Script

See all locations immediately:
```cmd
python discover_locations.py
```

Then manually add missing locations by creating monitors for them.

---

## What You'll See

### Startup Logs (With Extended Discovery):

```
================================================================================
Starting ArtsVision Monitor Application
================================================================================

Discovering API schema...
Found 47 entities
Event entity has 89 fields

Discovering all locations...
Checking for Location entity...
No Location entity found
Found 287 events in next 90 days (total: 2847)
Discovered 15 unique locations from events
Total locations discovered: 15
Locations: Alexis & Jim Pugh Theater, Dock A, Dock B, ...
Location discovery complete: 15 locations available

Running initial API poll...
Received 8 events from API
Processed 8 confirmed events from 5 locations
  Including 2 all-day events (active 24 hours)

Total locations in dropdown: 15
```

### Dashboard:

The "Location" dropdown when creating a monitor now shows **all 15 locations**, even if they don't have events today!

---

## Technical Details

### How Locations Are Stored

**During Startup:**
```python
# Query events for next 90 days
events = query_events(today, today + 90_days)

# Extract unique locations
locations = set()
for event in events:
    locations.add(event.location)

# Store persistently
database.save('all_locations', locations)
```

**During Daily Polls:**
```python
# Query today's events
todays_events = query_events(today, tomorrow)

# Merge with existing locations (never remove)
all_locations = existing_locations.union(new_locations)
```

**Result:** Locations accumulate over time and are never removed.

---

## Troubleshooting

### Still Missing Locations?

**Check 1: Increase date range**
```ini
LOCATION_DISCOVERY_DAYS=365
```

**Check 2: Run discovery script**
```cmd
python discover_locations.py
```
See what locations actually exist in the API.

**Check 3: Check event dates**
Maybe your events are scheduled more than 90 days out?

**Check 4: Check logs**
```
Discovered 15 unique locations from events
```
How many did it find?

### No Events in Date Range?

If you see:
```
Found 0 events in next 90 days
```

Then your events are either:
- Scheduled in the past
- Scheduled more than 90 days out
- Not in the system yet

**Solution:** Increase `LOCATION_DISCOVERY_DAYS` or add events to ArtsVision.

### Location Entity Exists?

If logs show:
```
Found location entities: ['Location']
Location: Found 47 location records
```

Then you have a dedicated Location entity! The app will use it automatically.

---

## Recommendations

### For Most Users:
```ini
LOCATION_DISCOVERY_DAYS=90
```
Good balance - finds most locations without long queries.

### For Far-Ahead Planning:
```ini
LOCATION_DISCOVERY_DAYS=365
```
If you schedule events many months in advance.

### For Immediate/Short-Term:
```ini
LOCATION_DISCOVERY_DAYS=30
```
If you only schedule events a month ahead.

---

## Example Scenarios

### Scenario 1: Arts Center with Varied Scheduling

**Configuration:**
```ini
LOCATION_DISCOVERY_DAYS=180
```

**Result:**
- Queries 6 months of events
- Finds all venues with scheduled shows
- Includes seasonal venues
- Dropdown has complete list

### Scenario 2: Venue with Far-Ahead Booking

**Configuration:**
```ini
LOCATION_DISCOVERY_DAYS=365
```

**Result:**
- Queries full year
- Captures all reserved dates
- Even infrequently-used spaces appear
- Complete venue list

### Scenario 3: Immediate Operations Only

**Configuration:**
```ini
LOCATION_DISCOVERY_DAYS=30
```

**Result:**
- Faster queries
- Just next month
- Main venues appear
- Can manually add others

---

## Summary

**Problem:** Only seeing locations with events today

**Solution:** Now searches 90+ days ahead

**Configuration:** `LOCATION_DISCOVERY_DAYS=90` in `.env`

**Benefit:** All locations appear in dropdown

**Script:** `discover_locations.py` to see what's available

**Restart and you'll see all your locations!** 🎭

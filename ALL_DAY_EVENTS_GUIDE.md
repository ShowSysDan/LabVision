# All-Day Event Support

## ✅ How It Works

All-day events (like loading bay reservations) are now **fully supported**!

### What Are All-Day Events?

Events in ArtsVision with:
- ❌ No start time
- ❌ No end time
- ✅ Just a date

**Examples:**
- Loading Bay Reservations
- Facility Holds
- Dark Days
- Equipment Reserves

---

## 🎯 How They're Processed

When the application finds an all-day event:

1. **Sets times to full day:**
   - Start: 12:00 AM (midnight)
   - End: 11:59 PM

2. **Marks it as all-day:**
   - `is_all_day: true` flag

3. **Processes normally:**
   - Monitor activates with PRE_SHOW_MINUTES before midnight
   - Monitor deactivates with POST_SHOW_MINUTES after 11:59 PM

---

## 📊 Monitor Behavior

### For All-Day Events:

**Example:** Loading Bay Reserved on Feb 6, 2026

**With default settings:**
- PRE_SHOW_MINUTES = 30
- POST_SHOW_MINUTES = 60

**Monitor Timeline:**
```
11:30 PM (Feb 5) → Monitor ACTIVATES (30 min before midnight)
12:00 AM (Feb 6) → Event "starts" (all-day begins)
11:59 PM (Feb 6) → Event "ends" (all-day ends)
12:59 AM (Feb 7) → Monitor DEACTIVATES (60 min after end)
```

**Result:** Monitor is active for ~25.5 hours total

---

## 🖥️ Dashboard Display

### Regular Event:
```
Event Name: Opening Night Gala
Time: 7:00 PM - 10:30 PM
```

### All-Day Event:
```
Event Name: Loading Bay Reserved
All-Day Event
```

**Note:** Times aren't shown for all-day events since they're active the entire day.

---

## 📝 Logs

You'll see:

```
Polling ArtsVision API...
Received 20 events from API
Processed 18 confirmed events from 8 locations
  Including 3 all-day events (active 24 hours)
  Skipped 2 canceled/released events
```

**Debug logs show:**
```
All-day event: Loading Bay Reserved at Dock A (active 24 hours)
```

---

## ⚙️ Configuration

All-day events work with your existing settings:

```ini
# .env
PRE_SHOW_MINUTES=30    # Monitor activates 30 min before midnight
POST_SHOW_MINUTES=60   # Monitor deactivates 60 min after 11:59 PM
```

### Want Different Timing for All-Day Events?

You can adjust when monitors activate/deactivate:

**Activate earlier:**
```ini
PRE_SHOW_MINUTES=120  # Activate 2 hours before (10 PM previous day)
```

**Deactivate later:**
```ini
POST_SHOW_MINUTES=180  # Deactivate 3 hours after (3 AM next day)
```

---

## 🔧 Technical Details

### How Dates Are Parsed:

1. **Get event date** from ArtsVision
2. **Parse date string** (e.g., "2026-02-06T00:00:00")
3. **Set times:**
   ```python
   in_time = date.replace(hour=0, minute=0, second=0)     # 12:00 AM
   out_time = date.replace(hour=23, minute=59, second=59)  # 11:59 PM
   ```

### Data Structure:

```json
{
  "location": "Dock A",
  "name": "Loading Bay Reserved",
  "in_time": "2026-02-06T00:00:00",
  "out_time": "2026-02-06T23:59:59",
  "is_all_day": true,
  "status": "Confirmed"
}
```

---

## 🎭 Use Cases

### Theater Holds
Monitor tracks when a theater is held all day (rehearsal, setup, etc.)

### Loading Bay Reservations
Monitor shows when loading docks are reserved

### Equipment Holds
Track when equipment/spaces are unavailable

### Dark Days
Monitor when venues are intentionally dark/closed

### Facility Maintenance
Track when spaces are out of service for maintenance

---

## 💡 Examples

### Scenario 1: Loading Bay All Day

**Event:** Loading Bay Reserved - Feb 6, 2026

**Monitor Settings:**
- Location: Dock A
- PRE_SHOW: 30 min
- POST_SHOW: 60 min

**Behavior:**
- 11:30 PM Feb 5 → ACTIVE (webhook fires if configured)
- All day Feb 6 → ACTIVE
- 12:59 AM Feb 7 → INACTIVE (webhook fires)

---

### Scenario 2: Regular Show Same Day

**Events on Feb 6:**
1. Loading Bay Reserved (all-day)
2. Evening Concert (7 PM - 10 PM)

**Monitor for Concert Hall:**
- 6:30 PM → ACTIVE (30 min before)
- 7:00 PM - 10:00 PM → ACTIVE (show running)
- 11:00 PM → INACTIVE (60 min after)

**Monitor for Dock A:**
- 11:30 PM Feb 5 → ACTIVE
- All day Feb 6 → ACTIVE
- 12:59 AM Feb 7 → INACTIVE

**Both monitors work independently!**

---

## ❓ FAQ

**Q: Will all-day events interfere with regular shows?**
A: No! Each monitor tracks one location independently.

**Q: Can I have both all-day and regular events at the same location?**
A: Yes! Monitor shows whichever event is currently happening.

**Q: Do all-day events trigger webhooks?**
A: Yes! Just like regular events.

**Q: What if I don't want all-day events?**
A: You can't currently filter them out, but you can:
- Not create monitors for those locations
- Or adjust the event status in ArtsVision

**Q: Can I change when all-day events activate?**
A: Yes, via PRE_SHOW_MINUTES and POST_SHOW_MINUTES in `.env`

---

## 🚀 Summary

**Before:** All-day events were skipped ❌

**Now:** All-day events are fully supported ✅

**Benefits:**
- ✅ Track loading bay reservations
- ✅ Monitor facility holds
- ✅ Automate all-day events
- ✅ Unified monitoring solution

**Display:**
- Shows "All-Day Event" on dashboard
- Hides specific times (since it's all day)
- Shows activation/deactivation countdowns

**No configuration needed** - works automatically! 🎉

---

## Example Output

```
=== Dashboard ===

Monitor: Dock A Loading
Location: Dock A
Status: ACTIVE 🟢

Current Event:
  Loading Bay Reserved
  All-Day Event
  Deactivates at 12:59 AM Feb 7 (in 14 hours)

Next Event:
  Equipment Delivery
  8:00 AM - 12:00 PM Feb 7
  Activates at 7:30 AM Feb 7 (in 31 hours)
```

Perfect for tracking your Dr. Phillips Performing Arts Center operations! 🎭

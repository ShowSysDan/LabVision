# Windows Testing Checklist

Quick reference for testing ArtsVision Monitor on Windows.

## Pre-Flight Check

```
□ Python 3.8+ installed
□ "Add Python to PATH" was checked during install
□ Can run: python --version
□ Have API key ready
□ Have .tar.gz file downloaded
```

## Installation (5 Minutes)

### Step 1: Extract Files
```
□ Right-click artsvision-monitor.tar.gz
□ Select "Extract All..."
□ Navigate to extracted folder
```

### Step 2: First Run
```
□ Double-click run.bat
□ Wait for: "WARNING: .env file not found!"
□ Window should pause - press any key
```

### Step 3: Configure
```
□ Open .env in Notepad
□ Replace API key: ARTSVISION_API_KEY=your-key-here
□ Save and close
```

### Step 4: Second Run
```
□ Double-click run.bat again
□ Wait for: "Dashboard will be available at: http://localhost:5000"
□ Leave window open
```

### Step 5: Access Dashboard
```
□ Open browser
□ Go to: http://localhost:5000
□ Dashboard should load
```

## Functional Testing

### Test 1: API Connection
```
□ Click "Refresh Now" button
□ Check Command Prompt window for:
  "Polling ArtsVision API..."
  "Received X events from API"
□ Pass: Events received
□ Fail: Check API key in .env
```

### Test 2: Schema Discovery
```
□ Open new browser tab
□ Go to: http://localhost:5000/api/schema
□ Should see JSON with entities and fields
□ Pass: JSON data visible
□ Fail: Check API connection
```

### Test 3: Location Discovery
```
□ In dashboard, click "+ Add Monitor"
□ Click "Location" dropdown
□ Should see list of locations
□ Pass: Locations listed
□ Fail: Wait 30 seconds and try again
```

### Test 4: Create Monitor
```
□ Fill in Monitor Name: "Test Monitor"
□ Select any location from dropdown
□ Click "Save Monitor"
□ Monitor card should appear on dashboard
□ Pass: Monitor card visible
□ Fail: Check Command Prompt for errors
```

### Test 5: Real-Time Updates
```
□ Leave dashboard open
□ Wait 1-2 minutes
□ Monitor status should update (if events exist)
□ Last update timestamp should change
□ Pass: Timestamp updates automatically
□ Fail: Check if server is still running
```

### Test 6: Monitor Edit/Delete
```
□ Click ✏️ edit button on test monitor
□ Change name to "Modified Test"
□ Click "Save Monitor"
□ Name should update on card
□ Click 🗑️ delete button
□ Confirm deletion
□ Monitor card should disappear
□ Pass: All operations work
□ Fail: Check browser console (F12)
```

### Test 7: Webhook (Optional)
```
□ Create new monitor
□ Enable webhook checkbox
□ Enter URL: https://webhook.site/unique-url
  (Get URL from https://webhook.site)
□ Set method: POST
□ Save monitor
□ Click "Test Webhook" button
□ Check webhook.site for received request
□ Pass: Request appears on webhook.site
□ Fail: Check URL is accessible
```

## Common Issues Quick Fix

### Issue: "Python is not recognized"
```
Fix:
□ Reinstall Python
□ Check "Add Python to PATH" during install
□ Restart Command Prompt
```

### Issue: Port 5000 already in use
```
Fix Option 1:
□ Close other applications using port 5000
□ Restart run.bat

Fix Option 2:
□ Edit app.py, change port to 5001
□ Access: http://localhost:5001
```

### Issue: No locations in dropdown
```
Fix:
□ Click "Refresh Now"
□ Wait 30 seconds
□ Check Command Prompt for API errors
□ Verify API key in .env
```

### Issue: Dashboard won't load
```
Fix:
□ Check Command Prompt still running
□ Look for errors in Command Prompt
□ Try: http://127.0.0.1:5000
□ Check Windows Firewall settings
```

### Issue: "Module not found" errors
```
Fix:
□ Close application (Ctrl+C)
□ Run: venv\Scripts\activate.bat
□ Run: pip install -r requirements.txt
□ Run: python app.py
```

## Performance Check

```
□ RAM usage < 150 MB (check Task Manager)
□ CPU usage < 5% when idle
□ Dashboard loads in < 2 seconds
□ Monitor updates in < 1 minute
□ No errors in Command Prompt
```

## Clean Shutdown

```
□ Close browser tabs
□ In Command Prompt: Press Ctrl+C
□ Wait for "Server stopped" message
□ Close Command Prompt window
```

## Production Readiness (Optional)

If deploying for actual use:

```
□ Change SECRET_KEY in .env
□ Set strong/unique value
□ Document monitor configurations
□ Set up regular backups of .db file
□ Consider running as Windows Service
□ Configure firewall rules
□ Set up monitoring/alerts
```

## Test Results

**Date:** _________________

**Tester:** _________________

**Python Version:** _________________

**Test Results:**
```
□ All tests passed
□ Some tests failed (note below)
□ Could not complete testing

Issues encountered:
_________________________________
_________________________________
_________________________________
_________________________________
```

**Notes:**
_________________________________
_________________________________
_________________________________
_________________________________

## Next Steps After Testing

### For Development/Testing:
```
□ Create monitors for your locations
□ Configure webhooks if needed
□ Test with real events
□ Monitor logs for issues
```

### For Production:
```
□ Set up as Windows Service (see WINDOWS_SETUP_GUIDE.md)
□ Configure production SECRET_KEY
□ Set up backup schedule
□ Document configuration
□ Train users on dashboard
```

## Quick Commands Reference

```batch
:: Navigate to folder
cd C:\path\to\artsvision-monitor

:: Run application
run.bat

:: Stop application
Ctrl + C in Command Prompt

:: View logs
:: (just look at Command Prompt window)

:: Reinstall dependencies
venv\Scripts\activate.bat
pip install -r requirements.txt

:: Reset database (WARNING: deletes all monitors)
del artsvision_monitors.db
python app.py
```

## Support Resources

**Files to Check:**
- WINDOWS_SETUP_GUIDE.md - Detailed setup instructions
- README.md - Full documentation
- QUICKSTART.md - Basic setup guide
- TROUBLESHOOTING section in WINDOWS_SETUP_GUIDE.md

**Useful URLs:**
- Dashboard: http://localhost:5000
- API Schema: http://localhost:5000/api/schema
- Locations: http://localhost:5000/api/locations
- Test Webhooks: https://webhook.site

**Log Locations:**
- Command Prompt window (live logs)
- Database: artsvision_monitors.db

---

## ✅ Testing Complete!

If all tests passed:
- You're ready to use ArtsVision Monitor
- Set up your actual monitors
- Configure webhooks as needed
- Enjoy automated theater monitoring!

If tests failed:
- Review WINDOWS_SETUP_GUIDE.md troubleshooting section
- Check Command Prompt for specific errors
- Verify API key is correct
- Try manual setup steps

**Good luck! 🎭**

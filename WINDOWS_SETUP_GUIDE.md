# Windows Setup Guide - ArtsVision Monitor

Complete guide for testing and running ArtsVision Monitor on Windows.

## Prerequisites

### 1. Install Python

**Download Python 3.8 or higher:**
1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.12.x" (or latest version)
3. **IMPORTANT**: Run the installer and check ✅ "Add Python to PATH"
4. Click "Install Now"

**Verify Installation:**
```cmd
python --version
```
Should show: `Python 3.12.x` (or your version)

### 2. Install Git (Optional - for updates)
Download from: https://git-scm-windows.github.io/

---

## Quick Start (3 Steps)

### Step 1: Extract the Archive

**Option A: Using Windows Explorer**
1. Right-click `artsvision-monitor.tar.gz`
2. Select "Extract All..." (or use 7-Zip/WinRAR)
3. Choose destination folder

**Option B: Using Command Line**
```cmd
:: If you have 7-Zip installed
"C:\Program Files\7-Zip\7z.exe" x artsvision-monitor.tar.gz
"C:\Program Files\7-Zip\7z.exe" x artsvision-monitor.tar
```

### Step 2: Run the Application

Open Command Prompt in the extracted folder:

**Method 1: Double-click the batch file**
1. Navigate to the `artsvision-monitor` folder
2. Double-click `run.bat`

**Method 2: Use Command Prompt**
```cmd
cd artsvision-monitor
run.bat
```

**First Run Output:**
```
Creating virtual environment...
Installing dependencies...
WARNING: .env file not found!
Copying .env.example to .env...
Please edit .env with your API credentials before running again.
Press any key to continue . . .
```

### Step 3: Configure and Run Again

1. Open `.env` file with Notepad:
   ```cmd
   notepad .env
   ```

2. Edit the API key:
   ```ini
   ARTSVISION_API_KEY=your-actual-api-key-here
   ```

3. Save and close

4. Run again:
   ```cmd
   run.bat
   ```

**Success Output:**
```
Starting server...
Discovering ArtsVision API schema...
Found 47 entities
Dashboard will be available at: http://localhost:5000
Press Ctrl+C to stop
```

5. Open browser to: **http://localhost:5000**

---

## Manual Setup (Step-by-Step)

If the batch file doesn't work, follow these manual steps:

### 1. Create Virtual Environment
```cmd
cd artsvision-monitor
python -m venv venv
```

### 2. Activate Virtual Environment
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` at the start of your command prompt:
```
(venv) C:\Users\YourName\artsvision-monitor>
```

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure Environment
```cmd
copy .env.example .env
notepad .env
```

Edit the API key and save.

### 5. Run the Application
```cmd
python app.py
```

### 6. Access Dashboard
Open browser: http://localhost:5000

---

## Windows-Specific Issues & Solutions

### Issue 1: "Python is not recognized"

**Problem:** Python not in PATH

**Solution:**
1. Find Python installation (usually `C:\Users\YourName\AppData\Local\Programs\Python\Python3xx`)
2. Add to PATH:
   - Search Windows for "Environment Variables"
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit" → "New"
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3xx`
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3xx\Scripts`
   - Click OK, restart Command Prompt

**Quick Test:**
```cmd
where python
```
Should show the Python path.

### Issue 2: "pip is not recognized"

**Solution:**
```cmd
python -m pip install --upgrade pip
```

### Issue 3: Port 5000 Already in Use

**Check what's using port 5000:**
```cmd
netstat -ano | findstr :5000
```

**Solution A: Kill the process**
```cmd
taskkill /PID [PID_NUMBER] /F
```

**Solution B: Use different port**

Edit `app.py`, change last line:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

Then access: http://localhost:5001

### Issue 4: Firewall Blocking

**Symptoms:** Can't access http://localhost:5000

**Solution:**
1. Windows Defender Firewall → Allow an app
2. Click "Change settings" → "Allow another app"
3. Browse to: `venv\Scripts\python.exe`
4. Check both Private and Public
5. Click Add

### Issue 5: "Permission Denied" Errors

**Solution:** Run Command Prompt as Administrator
1. Search for "cmd"
2. Right-click "Command Prompt"
3. Select "Run as administrator"

### Issue 6: Virtual Environment Not Activating

**Error:** `activate.bat` not found

**Solution:**
```cmd
:: Recreate virtual environment
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Issue 7: SSL/Certificate Errors

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution (Temporary - for testing only):**

Edit `api_poller.py`, add `verify=False` to requests:
```python
response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
```

**Better Solution:** Install certificates:
```cmd
pip install --upgrade certifi
```

---

## Testing the Application

### 1. Check if Server is Running

Open browser to: http://localhost:5000

You should see the dashboard.

### 2. Test API Key

Click "Refresh Now" button. Check the console output:
```
Polling ArtsVision API...
API Response Status: 200
Received 15 events from API
```

### 3. View Discovered Schema

Open: http://localhost:5000/api/schema

Should return JSON with entities and fields.

### 4. Add a Test Monitor

1. Click "+ Add Monitor"
2. Enter name: "Test Monitor"
3. Select a location from dropdown
4. Click "Save Monitor"

Monitor card should appear on dashboard.

### 5. Check Logs

Watch the Command Prompt window for:
```
[2026-02-06 15:30:00] Polling ArtsVision API...
[2026-02-06 15:30:01] Received 15 events from API
[2026-02-06 15:30:01] Processing 3 monitors...
```

---

## Running as Windows Service (Optional)

For production use, run as a Windows service:

### Option 1: Using NSSM (Recommended)

**Download NSSM:**
1. Download from: https://nssm.cc/download
2. Extract `nssm.exe` to `C:\nssm`

**Install Service:**
```cmd
cd C:\nssm
nssm install ArtsVisionMonitor "C:\path\to\artsvision-monitor\venv\Scripts\python.exe"
nssm set ArtsVisionMonitor AppDirectory "C:\path\to\artsvision-monitor"
nssm set ArtsVisionMonitor AppParameters "app.py"
nssm set ArtsVisionMonitor DisplayName "ArtsVision Monitor Dashboard"
nssm set ArtsVisionMonitor Description "Theater event monitoring dashboard"
nssm set ArtsVisionMonitor Start SERVICE_AUTO_START
nssm start ArtsVisionMonitor
```

**Manage Service:**
```cmd
:: Start
nssm start ArtsVisionMonitor

:: Stop
nssm stop ArtsVisionMonitor

:: View status
nssm status ArtsVisionMonitor

:: Uninstall
nssm remove ArtsVisionMonitor confirm
```

**View Logs:**
```cmd
nssm set ArtsVisionMonitor AppStdout "C:\path\to\artsvision-monitor\logs\service.log"
nssm set ArtsVisionMonitor AppStderr "C:\path\to\artsvision-monitor\logs\error.log"
```

### Option 2: Using Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "ArtsVision Monitor"
4. Trigger: "When the computer starts"
5. Action: "Start a program"
6. Program: `C:\path\to\artsvision-monitor\run.bat`
7. Finish

---

## Development/Testing Tips

### Keep Console Open
```cmd
:: Add this to end of run.bat to keep window open
pause
```

### View Detailed Logs
```cmd
:: Run with debug logging
set FLASK_DEBUG=1
python app.py
```

### Test Different Configurations

**Test with different API poll interval:**
Edit `.env`:
```ini
API_POLL_INTERVAL=300  # 5 minutes instead of 30
```

**Test webhook locally:**

Use a tool like [RequestBin](https://requestbin.com) or run a local test server:

```python
# test_webhook_server.py
from flask import Flask, request
app = Flask(__name__)

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    print("Received webhook!")
    print(request.json)
    return "OK"

if __name__ == '__main__':
    app.run(port=5001)
```

Run in separate Command Prompt:
```cmd
python test_webhook_server.py
```

Set webhook URL to: `http://localhost:5001/webhook`

### Access from Other Devices

**Find your local IP:**
```cmd
ipconfig
```

Look for "IPv4 Address" (e.g., 192.168.1.100)

**Access from phone/tablet:**
http://192.168.1.100:5000

**Note:** May need to allow through firewall (see Issue 4 above)

---

## Stopping the Application

### If Running in Command Prompt:
Press `Ctrl + C`

### If Running as Service:
```cmd
nssm stop ArtsVisionMonitor
```

### If Window is Closed:
Find and kill the process:
```cmd
tasklist | findstr python
taskkill /IM python.exe /F
```

---

## Updating to New Version

### Method 1: Clean Install
```cmd
:: Stop application (Ctrl+C or close window)

:: Backup your data
copy .env .env.backup
copy artsvision_monitors.db artsvision_monitors.db.backup

:: Extract new version to new folder
:: Copy back your config
copy .env.backup new-folder\.env
copy artsvision_monitors.db.backup new-folder\artsvision_monitors.db

:: Run new version
cd new-folder
run.bat
```

### Method 2: In-Place Update
```cmd
:: Stop application

:: Backup database
copy artsvision_monitors.db artsvision_monitors.db.backup

:: Extract new version over existing
:: (Select "Replace files" when prompted)

:: Run
run.bat
```

---

## Uninstalling

### 1. Stop the Application
```cmd
:: If running in console: Ctrl+C
:: If running as service:
nssm stop ArtsVisionMonitor
nssm remove ArtsVisionMonitor confirm
```

### 2. Delete Folder
```cmd
cd ..
rmdir /s /q artsvision-monitor
```

### 3. Clean Up (Optional)
```cmd
:: Remove Python packages (if not used by other apps)
pip uninstall -y Flask Flask-SocketIO Flask-SQLAlchemy APScheduler requests
```

---

## Getting Help

### Check Logs
Look at Command Prompt output for errors

### Common Error Messages

**"ModuleNotFoundError: No module named 'flask'"**
→ Virtual environment not activated or dependencies not installed
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**"Address already in use"**
→ Port 5000 is taken, use different port or kill existing process

**"Connection refused"**
→ ArtsVision API not reachable, check network and API_URL in .env

**"HTTP 403 Forbidden"**
→ Invalid API key, check ARTSVISION_API_KEY in .env

### Enable Debug Mode
Edit `.env`:
```ini
FLASK_DEBUG=1
```

Restart application to see detailed error messages.

### Test Individual Components

**Test Python:**
```cmd
python -c "print('Python works!')"
```

**Test Flask:**
```cmd
python -c "import flask; print(f'Flask {flask.__version__} installed')"
```

**Test Network:**
```cmd
ping av2.artsvision.net
```

**Test API Key:**
```cmd
curl -H "apikey: your-key-here" https://av2.artsvision.net/api/getentitynames
```

---

## Performance on Windows

### Typical Resource Usage:
- **RAM:** 50-100 MB
- **CPU:** < 1% (idle), 5-10% (during API poll)
- **Disk:** ~100 MB (including Python packages)
- **Network:** ~50 KB per API poll

### Improving Performance:

**Increase Poll Interval** (less frequent updates):
```ini
API_POLL_INTERVAL=3600  # 1 hour
```

**Reduce Monitor Count** (if you have 20+ monitors):
Only create monitors you actually need

**Use Production Server** (better than Flask development server):
```cmd
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

Note: On Windows, use `waitress` instead of `gunicorn`:
```cmd
pip install waitress
waitress-serve --port=5000 app:app
```

---

## Security Considerations

### For Testing (Local Network):
- Default settings are fine
- Dashboard accessible only from local network

### For Production (Internet Access):

1. **Use HTTPS** (nginx or IIS reverse proxy)
2. **Strong Secret Key** in `.env`
3. **Firewall Rules** (only allow necessary ports)
4. **Regular Updates** (check for new versions)
5. **Monitor Logs** (watch for suspicious activity)

### Recommended: Run Behind Reverse Proxy

Use IIS as reverse proxy:
1. Install IIS
2. Install URL Rewrite module
3. Install Application Request Routing
4. Configure reverse proxy to Python app

---

## Success Checklist

- [x] Python installed and in PATH
- [x] Application extracted
- [x] Virtual environment created
- [x] Dependencies installed
- [x] .env file configured with API key
- [x] Application starts without errors
- [x] Dashboard accessible at http://localhost:5000
- [x] API schema discovered (check logs)
- [x] Locations showing in dropdown
- [x] Test monitor created successfully
- [x] Events showing on monitor cards

**You're ready to use ArtsVision Monitor! 🎉**

---

## Quick Reference Commands

```cmd
:: Navigate to folder
cd C:\path\to\artsvision-monitor

:: Activate virtual environment
venv\Scripts\activate.bat

:: Install/update dependencies
pip install -r requirements.txt

:: Run application
python app.py

:: Or use batch file
run.bat

:: Stop application
Ctrl + C

:: Check Python version
python --version

:: Check installed packages
pip list

:: View logs
type logs\app.log

:: Test API connection
curl http://localhost:5000/api/schema
```

---

## Need More Help?

1. **Read the logs** in Command Prompt window
2. **Check README.md** for general documentation
3. **Try QUICKSTART.md** for basic setup
4. **Review troubleshooting section** above
5. **Test with** `/api/schema` **endpoint** to verify API connection

Good luck with your testing! 🚀

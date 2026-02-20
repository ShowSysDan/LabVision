# LabVision

A Python web application for monitoring theater events with real-time status updates, TV display outputs, webhook notifications, and a modern web interface.

## Features

- **Multi-Monitor Dashboard**: Create unlimited monitors for different theater locations
- **Real-Time Updates**: WebSocket-powered live status updates
- **TV Display Output**: 1920x1080 output pages for TVs near theaters/rooms
- **Display Theme Editor**: Customize colors, text sizes, and behavior with live preview
- **Auto-Discovery**: Automatically discovers all locations from the API
- **Webhook Support**: Configure HTTP POST/GET requests per monitor
- **Smart Activation**: Tracks pre-show and post-show windows
- **Event Timeline**: Shows current and upcoming events with countdowns
- **All Settings in UI**: API key, polling intervals, and all configuration via the dashboard (no config files to edit)
- **One-Command Install**: `sudo bash install.sh` sets up as a Debian/Ubuntu service

## Quick Start

### Option A: Install as a Service (Debian/Ubuntu - Recommended)

```bash
git clone <repo-url>
cd LabVision
sudo bash install.sh
```

This installs system dependencies, creates a virtual environment, installs Python packages, and sets up a systemd service that starts on boot and auto-restarts on crash.

After install, open `http://<your-ip>:5000` and click **Settings** to enter your API key.

### Option B: Run Manually

```bash
git clone <repo-url>
cd LabVision
bash run.sh
```

Dashboard: `http://localhost:5000`

### First-Time Setup

1. Open the dashboard in your browser
2. Click **Settings** in the header
3. Enter your API key and adjust settings as needed
4. Click **Save Settings**
5. Click **Refresh Now** to pull events immediately
6. Click **+ Add Monitor** to start monitoring locations

## TV Display Output

Each monitor can generate a 1920x1080 output page designed to be shown on a TV near a theater, loading dock, or room.

### Enabling TV Display

1. Edit a monitor (pencil icon)
2. Check **Enable TV Display Page**
3. Set **No Event Text** - what to show when nothing is happening:
   - `Dark` for a theater
   - `No Reservation` for a meeting room
   - `Available` for a loading dock
4. Toggle **Show Countdown to Next Event** to display "20min Till Reservation" style countdowns
5. Save - the display URL appears on the monitor card (e.g., `/display/main-theater`)

### What the Display Shows

**When active (event in progress):**
- Green background with event name, time range, and "Ends in X" countdown
- Long event names automatically scroll across the screen

**When inactive (no event):**
- Dark background with your custom no-event text
- Optional countdown to next reservation

### Display Theme Editor

Click **Display Theme** in the dashboard header to open the theme editor at `/settings/display-theme`.

Customize:
- **Colors**: Active/inactive backgrounds, accents, text colors, countdown color
- **Text Sizes**: Event name, time, no-event text, countdown, header, clock
- **Labels**: Change "IN USE" / "AVAILABLE" badge text
- **Scrolling**: Toggle auto-scroll for long event names
- **Live Preview**: See changes in real-time before saving (toggle between Active/Inactive views)

Theme changes apply globally to all TV display pages. Active displays reload the theme automatically every 5 minutes.

## Application Settings

All settings are configured through the dashboard UI (click **Settings**):

| Setting | Default | Description |
|---------|---------|-------------|
| API Key | (empty) | Your API key |
| API URL | `https://av2.artsvision.net/api/getdata` | API endpoint |
| Verify SSL | On | Disable for self-signed certificates |
| API Poll Interval | 1800s (30min) | How often to fetch events |
| Process Interval | 60s | How often to re-evaluate monitor states |
| Pre-Show Minutes | 30 | Activate monitor this many minutes before event |
| Post-Show Minutes | 60 | Keep active this many minutes after event |
| Filter Confirmed Only | On | Ignore tentative/canceled events |
| Discovery Days | 90 | How far ahead to look for locations |

Changes take effect on the next poll cycle without restarting the service.

## Service Management

After installing with `install.sh`:

```bash
# Check status
sudo systemctl status labvision

# Restart
sudo systemctl restart labvision

# Stop
sudo systemctl stop labvision

# View live logs
sudo journalctl -u labvision -f

# View last 50 log lines
sudo journalctl -u labvision --no-pager -n 50
```

The service:
- Starts automatically on boot
- Restarts automatically if it crashes (10s delay)
- Runs as the user who installed it (not root)

## Updating

To update to a new version:

```bash
cd LabVision
git pull
sudo systemctl restart labvision
```

Your database (monitors, settings, theme) is preserved across updates - only code files are updated via git.

## File Structure

```
LabVision/
├── app.py                          # Flask application and routes
├── api_poller.py                   # API polling logic
├── models.py                       # Database models (Monitor, SystemState)
├── config.py                       # Flask config and setting defaults
├── requirements.txt                # Python dependencies
├── install.sh                      # One-command Debian service installer
├── run.sh                          # Manual startup script
├── labvision.service               # Systemd service template (reference)
├── static/
│   ├── css/style.css               # Dashboard styles
│   └── js/dashboard.js             # Dashboard JavaScript
├── templates/
│   ├── dashboard.html              # Main dashboard
│   ├── display.html                # TV display output page (1920x1080)
│   └── display_theme_editor.html   # Display theme editor with preview
└── instance/
    └── labvision_monitors.db       # SQLite database (auto-created, not in git)
```

## API Endpoints

### Monitors
- `GET /api/monitors` - List all monitors
- `POST /api/monitors` - Create monitor
- `PUT /api/monitors/<id>` - Update monitor
- `DELETE /api/monitors/<id>` - Delete monitor
- `POST /api/test-webhook/<id>` - Test a monitor's webhook

### Display
- `GET /display/<monitor-slug>` - TV display page for a monitor
- `GET /api/display/<id>` - Display data JSON for a monitor

### Settings
- `GET /api/settings` - Get application settings
- `PUT /api/settings` - Update application settings
- `GET /api/settings/display-theme` - Get display theme
- `PUT /api/settings/display-theme` - Update display theme
- `POST /api/settings/display-theme/reset` - Reset theme to defaults

### Other
- `GET /api/locations` - Discovered locations
- `GET /api/schema` - ArtsVision API schema
- `POST /api/refresh` - Trigger manual API poll

## Troubleshooting

### No locations in dropdown
- Open **Settings** and verify your API key is correct
- Click **Refresh Now**
- Check logs: `sudo journalctl -u labvision -f`

### Monitor not activating
- Verify the event has "Confirmed" status in ArtsVision
- Check Pre-Show and Post-Show minutes in Settings
- Ensure event has valid start/end times

### TV display not updating
- Check the connection indicator in the bottom-right corner of the display
- The display auto-reconnects and polls every 2 minutes as a fallback
- Theme changes take up to 5 minutes to appear on active displays

### Webhook not firing
- Click **Test Webhook** on the monitor card
- Check that the webhook URL is reachable from the server
- Review logs for error details

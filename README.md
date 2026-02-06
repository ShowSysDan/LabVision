# ArtsVision Monitor Dashboard

A Python web application for monitoring ArtsVision theater events with real-time status updates, webhook notifications, and a modern web interface.

## Features

- 🎭 **Multi-Monitor Dashboard**: Create unlimited monitors for different theater locations
- 🔄 **Real-Time Updates**: WebSocket-powered live status updates
- 📍 **Auto-Discovery**: Automatically discovers all locations from ArtsVision API
- 🔔 **Webhook Support**: Configure HTTP POST/GET requests per monitor to integrate with other systems
- ⏰ **Smart Activation**: Tracks pre-show and post-show windows
- 📊 **Event Timeline**: Shows current and upcoming events with countdowns
- 🎨 **Modern UI**: Clean, responsive dashboard that works on all devices

## Key Features

- **No Hardcoded Locations**: All locations are discovered from the API automatically
- **Multiple Monitors**: Track as many locations as you need on a single dashboard
- **Webhook Integration**: Send status updates to external systems (lighting, AV, etc.)
- **Web Interface**: Access from any device with a browser
- **Real-Time Updates**: Live status changes without page refresh
- **Persistent Storage**: Monitor configurations saved in database

## Requirements

- Python 3.8+
- Modern web browser

## Installation

### 1. Clone or Download

Download this project to your server or computer.

### 2. Install Dependencies

```bash
cd artsvision-monitor
pip install -r requirements.txt
```

### 3. Configure

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```ini
ARTSVISION_API_KEY=your-api-key-here
ARTSVISION_API_URL=https://av2.artsvision.net/api/getdata

# Polling: How often to check for new events (default: 30 minutes)
API_POLL_INTERVAL=1800

# Processing: How often to update monitor states (default: 60 seconds)
PROCESS_INTERVAL=60

# Pre-show activation (default: 30 minutes before event)
PRE_SHOW_MINUTES=30

# Post-show deactivation (default: 60 minutes after event)
POST_SHOW_MINUTES=60
```

### 4. Run

```bash
python app.py
```

The dashboard will be available at: `http://localhost:5000`

## Usage

### Adding a Monitor

1. Click **"+ Add Monitor"** button
2. Give it a descriptive name (e.g., "Walt Disney Theater Monitor")
3. Select a location from the dropdown (auto-populated from API)
4. Optionally configure webhooks (see below)
5. Click **"Save Monitor"**

### Monitor Status

Each monitor card shows:

- **Status Indicator**: Green (ACTIVE) or Gray (Inactive) with pulsing dot
- **Current Event**: Name, time range, and deactivation countdown
- **Next Event**: Upcoming event with activation countdown
- **Location**: The theater/space being monitored

### Webhook Configuration

Webhooks allow you to send HTTP requests to other systems when a monitor's status changes (active ↔ inactive).

**Example Use Cases:**
- Trigger lighting scenes
- Activate AV equipment
- Send notifications
- Update building management systems
- Log events to external databases

**Configuration:**

1. Enable webhook checkbox
2. Enter webhook URL (e.g., `https://your-system.com/api/status`)
3. Choose method: POST or GET
4. (Optional) Add custom headers as JSON:
   ```json
   {
     "Authorization": "Bearer your-token",
     "Content-Type": "application/json"
   }
   ```
5. (Optional) Add body template for POST requests:
   ```
   {
     "location": "{location}",
     "active": {is_active},
     "event_name": "{current_event}"
   }
   ```

**Available Template Variables:**
- `{monitor_id}` - Monitor ID number
- `{monitor_name}` - Monitor display name
- `{location}` - Location name
- `{is_active}` - true/false active status
- `{current_event}` - Current event object (if any)
- `{next_event}` - Next event object (if any)
- `{timestamp}` - ISO timestamp of the change

**Testing Webhooks:**

Click the **"Test Webhook"** button to manually trigger the webhook and verify it's working.

## Architecture

### File Structure

```
artsvision-monitor/
├── app.py                 # Main Flask application
├── api_poller.py          # ArtsVision API polling logic
├── models.py              # Database models
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styles
│   └── js/
│       └── dashboard.js  # Frontend logic
└── templates/
    └── dashboard.html    # Dashboard HTML
```

### How It Works

1. **API Polling**: Every 30 minutes (configurable), polls ArtsVision API for today's events
2. **Event Processing**: Filters and processes events, discovering all locations
3. **Monitor Updates**: Every 60 seconds (configurable), checks each monitor's location against cached events
4. **Status Calculation**: Determines if monitor should be active based on:
   - Current time
   - Event start time - PRE_SHOW_MINUTES
   - Event end time + POST_SHOW_MINUTES
5. **Real-Time Sync**: WebSocket pushes updates to all connected browsers
6. **Webhook Triggers**: HTTP requests sent when monitor status changes

### Database

Uses SQLite by default (lightweight, no setup required). Tables:

- **monitor**: Monitor configurations and current state
- **system_state**: Cached API data and system settings

## API Endpoints

If you want to integrate programmatically:

- `GET /api/monitors` - Get all monitors
- `POST /api/monitors` - Create monitor
- `PUT /api/monitors/<id>` - Update monitor
- `DELETE /api/monitors/<id>` - Delete monitor
- `GET /api/locations` - Get discovered locations
- `GET /api/schema` - Get ArtsVision API schema (entities and Event fields)
- `POST /api/refresh` - Manual API refresh
- `POST /api/test-webhook/<id>` - Test webhook

### Schema Discovery

The application automatically discovers the ArtsVision API schema on startup:

```bash
# View discovered schema
curl http://localhost:5000/api/schema
```

This returns:
- All available entities (Event, Project, Resource, etc.)
- Event entity field definitions (names and types)
- Whether entities allow updates

This helps adapt to API changes and understand available data.

## Deployment

### Production Recommendations

1. **Use a production WSGI server** (not Flask's built-in dev server):
   ```bash
   pip install gunicorn eventlet
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```

2. **Set a secure SECRET_KEY** in `.env`

3. **Use PostgreSQL** for production (optional):
   ```ini
   DATABASE_URL=postgresql://user:pass@localhost/artsvision_monitors
   ```

4. **Set up as a system service** (systemd on Linux):

   Create `/etc/systemd/system/artsvision-monitor.service`:
   ```ini
   [Unit]
   Description=ArtsVision Monitor Dashboard
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/artsvision-monitor
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable artsvision-monitor
   sudo systemctl start artsvision-monitor
   ```

5. **Reverse proxy with Nginx** (optional):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

## Troubleshooting

### No locations showing up

- Check that API_KEY is correct in `.env`
- Verify API_URL is accessible
- Check logs for API errors
- Click "Refresh Now" to force immediate poll
- View `/api/schema` to see if Event fields were discovered

### Webhook not firing

- Click "Test Webhook" to verify configuration
- Check webhook URL is accessible
- Verify headers are valid JSON
- Check server logs for errors

### Monitor not activating

- Verify event has "Confirmed" status in ArtsVision
- Check PRE_SHOW_MINUTES and POST_SHOW_MINUTES settings
- Ensure event has valid start/end times
- Check that location name matches exactly
- View `/api/schema` to verify field names (e.g., "Start Time" vs "IN Time")

### Field mapping issues

If events aren't being detected correctly:
1. Visit `http://localhost:5000/api/schema`
2. Check the Event fields to see exact field names
3. Look for Start/End time fields, Location, Project name
4. Check server logs for field mapping warnings

## Customization

### Adjust Timing Windows

Edit in `.env`:
```ini
PRE_SHOW_MINUTES=45    # Activate 45 minutes before show
POST_SHOW_MINUTES=90   # Deactivate 90 minutes after show
```

### Change Polling Frequency

```ini
API_POLL_INTERVAL=900   # Poll every 15 minutes
PROCESS_INTERVAL=30     # Update monitors every 30 seconds
```

### Custom Styling

Edit `static/css/style.css` to customize colors, fonts, layout, etc.

## License

This project is provided as-is for use with ArtsVision theater management systems.

## Support

For issues or questions, please check:
1. This README
2. Application logs (console output)
3. Browser console (F12) for frontend errors

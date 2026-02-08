# Quick Start Guide

Get up and running in under 5 minutes.

## 1. Install

### Debian/Ubuntu (Recommended)
```bash
sudo bash install.sh
```
Done. The app is now running as a service and will start on boot.

### Manual / Other OS
```bash
bash run.sh
```

## 2. Configure API Key

1. Open `http://localhost:5000` (or your server's IP)
2. Click **Settings** in the header
3. Enter your ArtsVision API key
4. Click **Save Settings**
5. Click **Refresh Now** to pull events

## 3. Add Your First Monitor

1. Click **+ Add Monitor**
2. Name it (e.g., "Main Theater")
3. Select a location from the dropdown
4. Click **Save Monitor**

The monitor will now track events at that location in real-time.

## 4. Set Up a TV Display (Optional)

1. Edit the monitor (pencil icon)
2. Check **Enable TV Display Page**
3. Set **No Event Text** (e.g., "Dark" for a theater)
4. Enable **Show Countdown to Next Event**
5. Save - the display URL appears on the card
6. Open that URL on a TV's browser (e.g., `/display/main-theater`)

## 5. Customize the Display Theme (Optional)

1. Click **Display Theme** in the header
2. Adjust colors, text sizes, and labels
3. Toggle between Active/Inactive preview
4. Click **Save Theme**

## Service Commands

```bash
sudo systemctl status artsvision-monitor     # Check status
sudo systemctl restart artsvision-monitor     # Restart
sudo journalctl -u artsvision-monitor -f      # View logs
```

## Updating

```bash
git pull
sudo systemctl restart artsvision-monitor
```

Your database and settings are preserved - only code is updated.

## Troubleshooting

- **No locations?** Check your API key in Settings, then click Refresh Now
- **Can't connect?** Make sure the service is running (`systemctl status`)
- **Display not updating?** Check the connection dot in the bottom-right corner

See README.md for full documentation.

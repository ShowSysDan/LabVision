# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Python

Make sure you have Python 3.8 or higher installed:
```bash
python --version
```

If not installed, download from: https://www.python.org/downloads/

## 2. Run the Application

### On Linux/Mac:
```bash
./run.sh
```

### On Windows:
```
run.bat
```

The script will:
- Create a virtual environment
- Install dependencies
- Create a .env file (if needed)
- Start the server

## 3. Configure API Key

On first run, edit the `.env` file that was created:

```ini
ARTSVISION_API_KEY=your-api-key-here
```

Then run the script again.

## 4. Access Dashboard

Open your browser to:
```
http://localhost:5000
```

## 5. Add Your First Monitor

1. Click **"+ Add Monitor"**
2. Name it (e.g., "Main Theater")
3. Select a location from dropdown
4. Click **"Save Monitor"**

That's it! The monitor will now track events at that location.

## Next Steps

- **Add More Monitors**: Track multiple locations
- **Configure Webhooks**: Send status to other systems (see README.md)
- **Customize Settings**: Edit `.env` for timing adjustments

## Troubleshooting

**"No locations showing up"**
- Wait 30 seconds for initial API poll
- Click "Refresh Now" button
- Check API key in `.env`

**"Can't connect to localhost:5000"**
- Make sure the script is still running
- Check for error messages in the console
- Try a different port in app.py if 5000 is in use

**"Module not found" errors**
- Make sure you're using the virtual environment
- Run `pip install -r requirements.txt` manually

## Getting Help

See the full README.md for:
- Detailed configuration options
- Webhook examples
- Production deployment
- API documentation

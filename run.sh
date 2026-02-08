#!/bin/bash

# ArtsVision Monitor Dashboard - Manual Startup Script
# For development or running without systemd.
# For production, use: sudo bash install.sh

echo "Starting ArtsVision Monitor Dashboard..."
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo ""
echo "Starting server..."
echo "Dashboard will be available at: http://localhost:5000"
echo "Configure your API key via the Settings button in the dashboard."
echo "Press Ctrl+C to stop"
echo ""

python app.py

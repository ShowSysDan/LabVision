#!/bin/bash

# ArtsVision Monitor Dashboard - Startup Script

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

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env with your API credentials before running again."
    exit 1
fi

# Run the application
echo ""
echo "Starting server..."
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python app.py

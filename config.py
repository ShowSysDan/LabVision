import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///artsvision_monitors.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ArtsVision API
    ARTSVISION_API_KEY = os.environ.get('ARTSVISION_API_KEY', '823264392764')
    ARTSVISION_API_URL = os.environ.get('ARTSVISION_API_URL', 'https://av2.artsvision.net/api/getdata')
    
    # SSL Verification (set to False if ArtsVision uses self-signed certificate)
    ARTSVISION_VERIFY_SSL = os.environ.get('ARTSVISION_VERIFY_SSL', 'true').lower() == 'true'
    
    # Polling intervals
    API_POLL_INTERVAL = int(os.environ.get('API_POLL_INTERVAL', 1800))  # 30 minutes
    PROCESS_INTERVAL = int(os.environ.get('PROCESS_INTERVAL', 60))  # 60 seconds
    
    # Theater activation windows (in minutes)
    PRE_SHOW_MINUTES = int(os.environ.get('PRE_SHOW_MINUTES', 30))
    POST_SHOW_MINUTES = int(os.environ.get('POST_SHOW_MINUTES', 60))
    
    # Event filtering
    FILTER_CONFIRMED_ONLY = os.environ.get('FILTER_CONFIRMED_ONLY', 'true').lower() == 'true'
    
    # Date range for discovering locations (days into future)
    LOCATION_DISCOVERY_DAYS = int(os.environ.get('LOCATION_DISCOVERY_DAYS', '90'))
    
    # Display settings
    MAX_NEXT_EVENTS = int(os.environ.get('MAX_NEXT_EVENTS', 6))
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'

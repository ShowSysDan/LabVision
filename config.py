import os

class Config:
    """Flask infrastructure configuration (non-user-facing)"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///artsvision_monitors.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'


# Default application settings (stored in database via SystemState)
# These are used on first run before the user configures via the UI.
DEFAULT_APP_SETTINGS = {
    'api_key': '',
    'api_url': 'https://av2.artsvision.net/api/getdata',
    'verify_ssl': True,
    'api_poll_interval': 1800,       # 30 minutes
    'process_interval': 60,          # 60 seconds
    'pre_show_minutes': 30,
    'post_show_minutes': 60,
    'filter_confirmed_only': True,
    'location_discovery_days': 90,
}

import os
from dotenv import load_dotenv

# Load database credentials from database.env (ignored by git)
load_dotenv('database.env')


class Config:
    """Flask infrastructure configuration (non-user-facing)"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database — build PostgreSQL URI from database.env fields.
    # DATABASE_URL in the environment takes precedence (e.g. for Heroku/Docker).
    _db_host = os.environ.get('DB_HOST', 'localhost')
    _db_port = os.environ.get('DB_PORT', '5432')
    _db_name = os.environ.get('DB_NAME', 'labvision')
    _db_user = os.environ.get('DB_USER', 'labvision')
    _db_pass = os.environ.get('DB_PASSWORD', '')
    _db_schema = os.environ.get('DB_SCHEMA', 'public')

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        f"postgresql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Set search_path so all tables land in the configured schema.
    # db.create_all() will also create the schema if it doesn't exist (see init_app).
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'options': f'-csearch_path={_db_schema}'
        }
    }

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
    # Syslog
    'syslog_enabled': False,
    'syslog_host': '',
    'syslog_port': 514,
}

# Default display theme (stored in database via SystemState as 'display_theme')
DEFAULT_DISPLAY_THEME = {
    'active_bg': '#064e3b',
    'active_accent': '#10b981',
    'inactive_bg': '#1e293b',
    'inactive_accent': '#64748b',
    'text_color': '#f8fafc',
    'text_dim': '#94a3b8',
    'countdown_color': '#fbbf24',
    'event_name_size': 96,
    'event_time_size': 48,
    'no_event_text_size': 120,
    'countdown_size': 72,
    'header_name_size': 36,
    'clock_size': 28,
    'scroll_long_names': True,
    'active_label': 'IN USE',
    'inactive_label': 'AVAILABLE',
}

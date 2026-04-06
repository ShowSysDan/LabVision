from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Monitor, SystemState, get_app_settings, save_app_settings, get_display_theme, save_display_theme
from api_poller import ArtsVisionPoller
from config import Config, DEFAULT_APP_SETTINGS, DEFAULT_DISPLAY_THEME
import logging
import logging.handlers
import json
from datetime import datetime
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SYSLOG
# ============================================================================

_syslog_handler = None


def setup_syslog(settings):
    """Add or remove a UDP syslog handler based on current settings."""
    global _syslog_handler
    root = logging.getLogger()

    if _syslog_handler:
        root.removeHandler(_syslog_handler)
        _syslog_handler = None

    if settings.get('syslog_enabled') and settings.get('syslog_host'):
        host = settings['syslog_host'].strip()
        port = int(settings.get('syslog_port') or 514)
        try:
            handler = logging.handlers.SysLogHandler(address=(host, port))
            handler.setFormatter(logging.Formatter(
                'LabVision %(levelname)s %(name)s: %(message)s'
            ))
            root.addHandler(handler)
            _syslog_handler = handler
            logger.info(f"Syslog enabled → {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to set up syslog ({host}:{port}): {e}")


# ============================================================================
# IN-MEMORY LOG BUFFER (for debug page)
# ============================================================================

class MemoryLogHandler(logging.Handler):
    """Stores recent log entries in a deque for the debug page"""
    def __init__(self, capacity=500):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record):
        self.buffer.append({
            'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': self.format(record)
        })

    def get_entries(self, level=None, limit=200):
        entries = list(self.buffer)
        if level:
            entries = [e for e in entries if e['level'] == level.upper()]
        return entries[-limit:]

log_buffer = MemoryLogHandler(capacity=500)
log_buffer.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_buffer)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'], cors_allowed_origins="*")

# Initialize API poller (settings loaded from DB on each poll cycle)
poller = ArtsVisionPoller()

# Initialize scheduler
scheduler = BackgroundScheduler()


# ============================================================================
# SCHEDULED TASKS
# ============================================================================

def poll_api_task():
    """Background task to poll ArtsVision API"""
    with app.app_context():
        logger.info("Running scheduled API poll...")
        success = poller.poll_api()
        if success:
            # Immediately process monitors after successful poll
            process_monitors_task()


def process_monitors_task():
    """Background task to process monitor states"""
    with app.app_context():
        logger.info("Running scheduled monitor processing...")
        poller.process_monitors()

        # Emit update to all connected clients
        monitors = Monitor.query.filter_by(enabled=True).order_by(Monitor.order).all()
        socketio.emit('monitors_update', {
            'monitors': [m.to_dict() for m in monitors],
            'timestamp': datetime.utcnow().isoformat()
        })


def reschedule_jobs():
    """Reschedule polling jobs based on current database settings"""
    settings = get_app_settings()
    api_interval = int(settings.get('api_poll_interval', 1800))
    process_interval = int(settings.get('process_interval', 60))

    try:
        scheduler.reschedule_job('api_poll', trigger='interval', seconds=api_interval)
        logger.info(f"API poll rescheduled: every {api_interval} seconds")
    except Exception as e:
        logger.error(f"Error rescheduling api_poll: {e}")

    try:
        scheduler.reschedule_job('process_monitors', trigger='interval', seconds=process_interval)
        logger.info(f"Monitor processing rescheduled: every {process_interval} seconds")
    except Exception as e:
        logger.error(f"Error rescheduling process_monitors: {e}")


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/display/<path:monitor_slug>')
def display_page(monitor_slug):
    """TV display output page for a monitor (1920x1080 optimized)"""
    # Find monitor by slug (name lowercased with spaces replaced by hyphens)
    monitors = Monitor.query.filter_by(display_enabled=True).all()
    monitor = None
    for m in monitors:
        slug = m.name.lower().replace(' ', '-')
        if slug == monitor_slug.lower():
            monitor = m
            break

    if not monitor:
        abort(404)

    return render_template('display.html', monitor=monitor)


@app.route('/api/display/<int:monitor_id>')
def get_display_data(monitor_id):
    """Get live display data for a monitor (used by display page polling)"""
    monitor = Monitor.query.get_or_404(monitor_id)
    data = monitor.to_dict()
    return jsonify(data)


@app.route('/settings/display-theme')
def display_theme_editor():
    """Display theme editor page with live preview"""
    return render_template('display_theme_editor.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/monitors', methods=['GET'])
def get_monitors():
    """Get all monitors"""
    monitors = Monitor.query.order_by(Monitor.order).all()
    return jsonify({
        'monitors': [m.to_dict() for m in monitors],
        'last_api_poll': SystemState.get('last_api_poll')
    })


@app.route('/api/monitors', methods=['POST'])
def create_monitor():
    """Create a new monitor"""
    data = request.json

    try:
        monitor = Monitor(
            name=data['name'],
            location=data['location'],
            webhook_enabled=data.get('webhook_enabled', False),
            webhook_url=data.get('webhook_url'),
            webhook_method=data.get('webhook_method', 'POST'),
            webhook_body_template=data.get('webhook_body_template'),
            enabled=data.get('enabled', True),
            order=Monitor.query.count(),
            display_enabled=data.get('display_enabled', False),
            no_event_text=data.get('no_event_text', 'No Event'),
            show_countdown=data.get('show_countdown', True),
            pre_show_minutes=data.get('pre_show_minutes') or None,
            post_show_minutes=data.get('post_show_minutes') or None,
            qsys_control_name=data.get('qsys_control_name') or None,
            public_private_filter=data.get('public_private_filter', 'any'),
            ticketed_filter=data.get('ticketed_filter', 'any'),
        )

        if data.get('webhook_headers'):
            monitor.set_webhook_headers(data['webhook_headers'])

        db.session.add(monitor)
        db.session.commit()

        logger.info(f"Created monitor: {monitor.name} ({monitor.location})")

        # Emit update to all clients
        socketio.emit('monitor_created', monitor.to_dict())

        return jsonify(monitor.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating monitor: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@app.route('/api/monitors/<int:monitor_id>', methods=['PUT'])
def update_monitor(monitor_id):
    """Update a monitor"""
    monitor = Monitor.query.get_or_404(monitor_id)
    data = request.json

    try:
        monitor.name = data.get('name', monitor.name)
        monitor.location = data.get('location', monitor.location)
        monitor.webhook_enabled = data.get('webhook_enabled', monitor.webhook_enabled)
        monitor.webhook_url = data.get('webhook_url', monitor.webhook_url)
        monitor.webhook_method = data.get('webhook_method', monitor.webhook_method)
        monitor.webhook_body_template = data.get('webhook_body_template', monitor.webhook_body_template)
        monitor.enabled = data.get('enabled', monitor.enabled)
        monitor.display_enabled = data.get('display_enabled', monitor.display_enabled)
        monitor.no_event_text = data.get('no_event_text', monitor.no_event_text)
        monitor.show_countdown = data.get('show_countdown', monitor.show_countdown)
        if 'pre_show_minutes' in data:
            monitor.pre_show_minutes = data['pre_show_minutes'] or None
        if 'post_show_minutes' in data:
            monitor.post_show_minutes = data['post_show_minutes'] or None
        if 'qsys_control_name' in data:
            monitor.qsys_control_name = data['qsys_control_name'] or None
        if 'public_private_filter' in data:
            monitor.public_private_filter = data['public_private_filter'] or 'any'
        if 'ticketed_filter' in data:
            monitor.ticketed_filter = data['ticketed_filter'] or 'any'

        if 'webhook_headers' in data:
            monitor.set_webhook_headers(data['webhook_headers'])

        db.session.commit()

        logger.info(f"Updated monitor: {monitor.name}")

        # Emit update to all clients
        socketio.emit('monitor_updated', monitor.to_dict())

        return jsonify(monitor.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating monitor: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@app.route('/api/monitors/<int:monitor_id>', methods=['DELETE'])
def delete_monitor(monitor_id):
    """Delete a monitor"""
    monitor = Monitor.query.get_or_404(monitor_id)

    try:
        db.session.delete(monitor)
        db.session.commit()

        logger.info(f"Deleted monitor: {monitor.name}")

        # Emit update to all clients
        socketio.emit('monitor_deleted', {'id': monitor_id})

        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting monitor: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all discovered locations"""
    locations = SystemState.get('all_locations', [])
    return jsonify({
        'locations': sorted(locations)
    })


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get discovered API schema (entities and Event fields)"""
    entities = SystemState.get('available_entities', [])
    event_metadata = SystemState.get('event_metadata', [])

    # Extract Event fields if available
    event_fields = []
    if event_metadata and len(event_metadata) > 0:
        event_fields = event_metadata[0].get('Fields', [])

    return jsonify({
        'entities': entities,
        'event_entity': {
            'fields': event_fields,
            'field_count': len(event_fields),
            'allow_update': event_metadata[0].get('AllowIndividualUpdate', False) if event_metadata else False
        }
    })


@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    """Manually trigger full discovery and API poll"""
    try:
        settings = get_app_settings()
        if not settings.get('api_key'):
            return jsonify({'status': 'error', 'message': 'No API key configured'}), 400

        # Run full discovery (same as init_app does on startup)
        logger.info("Manual refresh: discovering API schema...")
        try:
            poller.discover_api_schema()
        except Exception as e:
            logger.warning(f"Schema discovery failed: {e}")

        logger.info("Manual refresh: discovering all locations...")
        try:
            locations = poller.discover_all_locations()
            logger.info(f"Manual refresh: found {len(locations)} locations")
        except Exception as e:
            logger.warning(f"Location discovery failed: {e}")

        # Poll today's events and process monitors
        poll_api_task()
        return jsonify({'status': 'success', 'message': 'Full refresh complete'})
    except Exception as e:
        logger.error(f"Error in manual refresh: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/test-webhook/<int:monitor_id>', methods=['POST'])
def test_webhook(monitor_id):
    """Test webhook for a monitor"""
    monitor = Monitor.query.get_or_404(monitor_id)

    try:
        if not monitor.webhook_enabled or not monitor.webhook_url:
            return jsonify({'error': 'Webhook not configured'}), 400

        # Force trigger webhook
        poller._trigger_webhook(monitor)

        return jsonify({'status': 'success', 'message': 'Webhook triggered'})

    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# QSYS API
# ============================================================================

def _fmt_time(iso_str):
    """Format an ISO datetime string to HH:MM for QSYS display."""
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str).strftime('%H:%M')
    except Exception:
        return None


def _countdown_str(iso_str, now):
    """Return a human-readable countdown string from now to iso_str."""
    if not iso_str:
        return None
    try:
        target = datetime.fromisoformat(iso_str)
        total_mins = int((target - now).total_seconds() / 60)
        if total_mins < 0:
            return 'Past'
        hours, mins = divmod(total_mins, 60)
        return f"{hours}h {mins}m" if hours else f"{mins}m"
    except Exception:
        return None


@app.route('/api/qsys/status', methods=['GET'])
def get_qsys_status():
    """
    QSYS-optimized endpoint.

    Returns a lean JSON payload keyed by QSYS control name so the Lua script
    can loop the list, set Controls[theater.control].Boolean = theater.is_active,
    and drop status_text straight into a text control.

    Only monitors that have a qsys_control_name configured are included.
    """
    monitors = Monitor.query.filter_by(enabled=True).order_by(Monitor.order).all()
    now = datetime.now()
    last_api_poll = SystemState.get('last_api_poll')

    theaters = []
    for monitor in monitors:
        if not monitor.qsys_control_name:
            continue

        current_ev = None
        if monitor.current_event:
            ev = json.loads(monitor.current_event)
            current_ev = {
                'name': ev.get('name', ''),
                'in_time': _fmt_time(ev.get('in_time')),
                'out_time': _fmt_time(ev.get('out_time')),
                'deactivates_at': _fmt_time(ev.get('deactivation_time')),
                'deactivates_countdown': _countdown_str(ev.get('deactivation_time'), now),
            }

        next_ev = None
        if monitor.next_event:
            ev = json.loads(monitor.next_event)
            next_ev = {
                'name': ev.get('name', ''),
                'in_time': _fmt_time(ev.get('in_time')),
                'out_time': _fmt_time(ev.get('out_time')),
                'activates_at': _fmt_time(ev.get('activation_time')),
                'activates_countdown': _countdown_str(ev.get('activation_time'), now),
            }

        theaters.append({
            'control': monitor.qsys_control_name,
            'monitor_id': monitor.id,
            'name': monitor.name,
            'is_active': monitor.is_active,
            'current_event': current_ev,
            'next_event': next_ev,
        })

    status_text = poller.generate_qsys_status_text(theaters, last_api_poll)

    return jsonify({
        'timestamp': now.isoformat(),
        'last_api_poll': last_api_poll,
        'status_text': status_text,
        'theaters': theaters,
    })


# ============================================================================
# SETTINGS API
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get application settings"""
    settings = get_app_settings()
    # Mask the API key for display (show last 4 chars only)
    masked = dict(settings)
    if masked.get('api_key'):
        key = masked['api_key']
        masked['api_key_masked'] = ('*' * max(0, len(key) - 4)) + key[-4:] if len(key) > 4 else key
    else:
        masked['api_key_masked'] = ''
    return jsonify(masked)


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update application settings"""
    data = request.json

    try:
        current = get_app_settings()
        old_api_key = current.get('api_key', '')

        # Update each setting if provided
        for key in DEFAULT_APP_SETTINGS:
            if key in data:
                current[key] = data[key]

        # Special handling: if api_key is empty/placeholder, keep existing
        if 'api_key' in data:
            if data['api_key'] and not data['api_key'].startswith('*'):
                current['api_key'] = data['api_key']
            # else keep existing key

        save_app_settings(current)

        # Reschedule jobs if intervals changed
        reschedule_jobs()

        # Reconfigure syslog if those settings changed
        setup_syslog(current)

        logger.info("Application settings updated")

        # If API key was set or changed, trigger full discovery
        new_api_key = current.get('api_key', '')
        if new_api_key and new_api_key != old_api_key:
            logger.info("API key changed — running discovery and initial poll...")
            try:
                poller.discover_api_schema()
            except Exception as e:
                logger.warning(f"Schema discovery failed: {e}")
            try:
                poller.discover_all_locations()
            except Exception as e:
                logger.warning(f"Location discovery failed: {e}")
            try:
                poller.poll_api()
                poller.process_monitors()
            except Exception as e:
                logger.warning(f"Initial poll failed: {e}")

        return jsonify({'status': 'success', 'message': 'Settings saved'})

    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


# ============================================================================
# DISPLAY THEME API
# ============================================================================

@app.route('/api/settings/display-theme', methods=['GET'])
def get_display_theme_settings():
    """Get display theme settings"""
    theme = get_display_theme()
    return jsonify(theme)


@app.route('/api/settings/display-theme', methods=['PUT'])
def update_display_theme():
    """Update display theme settings"""
    data = request.json

    try:
        current = get_display_theme()
        for key in DEFAULT_DISPLAY_THEME:
            if key in data:
                current[key] = data[key]
        save_display_theme(current)

        logger.info("Display theme updated")
        return jsonify({'status': 'success', 'message': 'Theme saved'})

    except Exception as e:
        logger.error(f"Error updating display theme: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@app.route('/api/settings/display-theme/reset', methods=['POST'])
def reset_display_theme():
    """Reset display theme to defaults"""
    try:
        save_display_theme(DEFAULT_DISPLAY_THEME)
        logger.info("Display theme reset to defaults")
        return jsonify(DEFAULT_DISPLAY_THEME)
    except Exception as e:
        logger.error(f"Error resetting display theme: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


# ============================================================================
# DEBUG PAGE
# ============================================================================

@app.route('/debug')
def debug_page():
    """Debug page showing logs, system state, and API diagnostics"""
    return render_template('debug.html')


@app.route('/api/debug/logs', methods=['GET'])
def get_debug_logs():
    """Get recent log entries"""
    level = request.args.get('level')
    limit = int(request.args.get('limit', 200))
    entries = log_buffer.get_entries(level=level, limit=limit)
    return jsonify({'entries': entries, 'total': len(log_buffer.buffer)})


@app.route('/api/debug/state', methods=['GET'])
def get_debug_state():
    """Get current system state for debugging"""
    settings = get_app_settings()
    # Mask API key
    if settings.get('api_key'):
        key = settings['api_key']
        settings['api_key'] = ('*' * max(0, len(key) - 4)) + key[-4:] if len(key) > 4 else '****'

    locations = SystemState.get('all_locations', [])
    cached_events = SystemState.get('cached_events', [])
    last_poll = SystemState.get('last_api_poll')
    entities = SystemState.get('available_entities', [])
    event_metadata = SystemState.get('event_metadata', [])

    monitors = Monitor.query.order_by(Monitor.order).all()

    # Summarize events by location
    events_by_location = {}
    for ev in cached_events:
        loc = ev.get('location', 'Unknown')
        events_by_location[loc] = events_by_location.get(loc, 0) + 1

    return jsonify({
        'settings': settings,
        'locations_count': len(locations),
        'locations': sorted(locations),
        'cached_events_count': len(cached_events),
        'events_by_location': events_by_location,
        'last_api_poll': last_poll,
        'entities': entities,
        'event_field_count': len(event_metadata[0].get('Fields', [])) if event_metadata else 0,
        'monitors': [{
            'id': m.id,
            'name': m.name,
            'location': m.location,
            'enabled': m.enabled,
            'is_active': m.is_active,
            'display_enabled': m.display_enabled,
            'last_updated': m.last_updated.isoformat() if m.last_updated else None
        } for m in monitors],
        'scheduler_jobs': [{
            'id': job.id,
            'next_run': str(job.next_run_time) if job.next_run_time else None,
            'trigger': str(job.trigger)
        } for job in scheduler.get_jobs()]
    })


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')

    # Send current monitor states
    monitors = Monitor.query.filter_by(enabled=True).order_by(Monitor.order).all()
    emit('monitors_update', {
        'monitors': [m.to_dict() for m in monitors],
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

def init_app():
    """Initialize the application"""
    with app.app_context():
        # Attempt to create the target schema if it's not 'public'.
        # This may fail if the DB user lacks CREATE SCHEMA privilege — in that
        # case a DBA should run:
        #   CREATE SCHEMA IF NOT EXISTS <schema>;
        #   GRANT ALL ON SCHEMA <schema> TO <user>;
        import os
        schema = os.environ.get('DB_SCHEMA', 'public')
        if schema != 'public':
            try:
                db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
                db.session.commit()
                logger.info(f"Schema '{schema}' ready")
            except Exception as e:
                db.session.rollback()
                logger.warning(
                    f"Could not auto-create schema '{schema}' (may already exist or "
                    f"user lacks privilege — ask your DBA): {e}"
                )

        # Create database tables
        db.create_all()

        # Seed default settings if none exist
        if not SystemState.get('app_settings'):
            logger.info("No settings found, seeding defaults...")
            save_app_settings(DEFAULT_APP_SETTINGS)

        # Load settings for startup
        settings = get_app_settings()

        # Configure syslog if enabled
        setup_syslog(settings)
        api_interval = int(settings.get('api_poll_interval', 1800))
        process_interval = int(settings.get('process_interval', 60))

        # Only run API operations if an API key is configured
        if settings.get('api_key'):
            # Discover API schema (entities and fields)
            logger.info("Discovering API schema...")
            try:
                poller.discover_api_schema()
            except Exception as e:
                logger.warning(f"Could not discover API schema: {str(e)}")
                logger.info("Continuing with default configuration...")

            # Discover all locations from extended date range
            logger.info("Discovering all locations...")
            try:
                locations = poller.discover_all_locations()
                logger.info(f"Location discovery complete: {len(locations)} locations available")
            except Exception as e:
                logger.warning(f"Could not discover all locations: {str(e)}")
                logger.info("Will discover locations from today's events only...")

            # Initial API poll
            logger.info("Running initial API poll...")
            poller.poll_api()
            poller.process_monitors()
        else:
            logger.info("No API key configured. Configure via Settings in the dashboard.")

        # Schedule recurring tasks
        scheduler.add_job(
            poll_api_task,
            'interval',
            seconds=api_interval,
            id='api_poll'
        )

        scheduler.add_job(
            process_monitors_task,
            'interval',
            seconds=process_interval,
            id='process_monitors'
        )

        scheduler.start()
        logger.info("Scheduler started")
        logger.info(f"API polling every {api_interval} seconds")
        logger.info(f"Monitor processing every {process_interval} seconds")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    init_app()
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

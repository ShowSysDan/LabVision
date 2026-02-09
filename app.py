from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Monitor, SystemState, get_app_settings, save_app_settings, get_display_theme, save_display_theme
from api_poller import ArtsVisionPoller
from config import Config, DEFAULT_APP_SETTINGS, DEFAULT_DISPLAY_THEME
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            show_countdown=data.get('show_countdown', True)
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
    """Manually trigger API poll and monitor processing"""
    try:
        poll_api_task()
        return jsonify({'status': 'success', 'message': 'Refresh triggered'})
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

        logger.info("Application settings updated")
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
        # Create database tables
        db.create_all()

        # Seed default settings if none exist
        if not SystemState.get('app_settings'):
            logger.info("No settings found, seeding defaults...")
            save_app_settings(DEFAULT_APP_SETTINGS)

        # Load settings for startup
        settings = get_app_settings()
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
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

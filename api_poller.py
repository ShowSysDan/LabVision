import requests
import logging
from datetime import datetime, timedelta
from models import db, Monitor, SystemState, get_app_settings
import json
import urllib3

logger = logging.getLogger(__name__)


class ArtsVisionPoller:
    """Poll ArtsVision API and process events"""

    def __init__(self):
        self.api_key = ''
        self.api_base_url = ''
        self.api_url = ''
        self.pre_show_minutes = 30
        self.post_show_minutes = 60
        self.verify_ssl = True
        self.filter_confirmed_only = True
        self.location_discovery_days = 90
        self.cached_events = []
        self.all_locations = set()
        self.event_metadata = None

    def reload_settings(self):
        """Reload settings from database before each operation"""
        settings = get_app_settings()

        self.api_key = settings.get('api_key', '')
        api_url = settings.get('api_url', 'https://av2.artsvision.net/api/getdata')
        self.api_url = api_url
        self.api_base_url = api_url.replace('/getdata', '').rstrip('/')
        self.pre_show_minutes = int(settings.get('pre_show_minutes', 30))
        self.post_show_minutes = int(settings.get('post_show_minutes', 60))
        self.verify_ssl = settings.get('verify_ssl', True)
        self.filter_confirmed_only = settings.get('filter_confirmed_only', True)
        self.location_discovery_days = int(settings.get('location_discovery_days', 90))

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_api_request(self, endpoint, method='GET', payload=None):
        """
        Make request to ArtsVision API with proper error handling.

        All API responses have structure: {"Status": 0/3, "Data": ...}
        Status 0 = success, Status 3 = error
        """
        try:
            url = f"{self.api_base_url}/{endpoint}"

            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30, verify=self.verify_ssl)
            else:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30,
                    verify=self.verify_ssl
                )

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            data = response.json()

            # Check API-level status (0 = success, 3 = error)
            if data.get('Status') == 3:
                logger.error(f"API Error: {data.get('Data')}")
                return None
            elif data.get('Status') == 0:
                return data.get('Data')
            else:
                logger.warning(f"Unknown API status: {data.get('Status')}")
                return None

        except Exception as e:
            logger.error(f"Error making API request to {endpoint}: {str(e)}", exc_info=True)
            return None

    def get_entity_names(self):
        """
        Get list of all available entity names from API.
        Endpoint: GET /api/getentitynames
        Returns: List of entity name strings
        """
        logger.info("Fetching entity names from API...")
        entity_names = self._make_api_request('getentitynames', method='GET')

        if entity_names:
            logger.info(f"Found {len(entity_names)} entities")
            SystemState.set('available_entities', entity_names)

        return entity_names or []

    def get_metadata(self, entity_name=None, fields_info=True):
        """
        Get metadata for entities including field definitions.
        Endpoint: GET /api/getmetadata?startWithEntity=X&fieldsInfo=true
        """
        logger.info(f"Fetching metadata for entity: {entity_name or 'all'}")

        params = []
        if entity_name:
            params.append(f"startWithEntity={entity_name}")
        params.append(f"fieldsInfo={'true' if fields_info else 'false'}")

        endpoint = f"getmetadata?{'&'.join(params)}" if params else 'getmetadata'
        metadata = self._make_api_request(endpoint, method='GET')

        if metadata and entity_name == 'Event':
            self.event_metadata = metadata
            SystemState.set('event_metadata', metadata)

            if metadata and len(metadata) > 0:
                fields = metadata[0].get('Fields', [])
                field_names = [f['Name'] for f in fields]
                logger.info(f"Event entity has {len(field_names)} fields")
                logger.debug(f"Available Event fields: {', '.join(field_names)}")

        return metadata or []

    def poll_api(self):
        """Fetch events from ArtsVision API"""
        try:
            self.reload_settings()
            if not self.api_key:
                logger.warning("No API key configured. Skipping poll. Configure via Settings in the dashboard.")
                return False
            logger.info("Polling ArtsVision API...")

            # Fetch from yesterday through tomorrow so that events starting before
            # midnight but ending (or still within their post-show window) after
            # midnight are included in monitor calculations.
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")

            filters = [
                {
                    "field": "Date",
                    "operator": "GreaterOrEqual",
                    "value": yesterday
                },
                {
                    "field": "Date",
                    "operator": "Less",
                    "value": tomorrow
                }
            ]

            if self.filter_confirmed_only:
                filters.append({
                    "field": "Event Status",
                    "operator": "Equal",
                    "value": "Confirmed"
                })

            payload = {
                "xml": False,
                "flatten": False,
                "entities": [
                    {
                        "entity": "Event",
                        "firstRowIndex": 0,
                        "rowsCount": 200,
                        "columns": [],
                        "filters": filters,
                        "orderby": [],
                        "include": []
                    }
                ]
            }

            data = self._make_api_request('getdata', method='POST', payload=payload)

            if data:
                self.process_api_response(data)
                return True
            else:
                logger.error("Failed to get data from API")
                return False

        except Exception as e:
            logger.error(f"Error polling API: {str(e)}", exc_info=True)
            return False

    def process_api_response(self, data):
        """
        Process API response and extract events.

        Args:
            data: The Data portion of API response (Status/Data wrapper already handled)
                  This is an array of ApiDataEntity objects
        """
        try:
            if not data or len(data) == 0:
                logger.warning("No data in API response")
                return

            data_entity = data[0]
            rows = data_entity.get('Rows', [])

            logger.info(f"Received {len(rows)} events from API")
            logger.debug(f"Total count: {data_entity.get('TotalCount')}, Returned: {data_entity.get('Count')}")

            events = []
            locations = set()
            all_day_count = 0
            skipped_canceled = 0

            for row in rows:
                if not row or not row.get('Data'):
                    continue

                event_data = row['Data']

                event_status = event_data.get('Event Status', '')
                if event_status and event_status.lower() in ['canceled', 'cancelled', 'released', 'tentative']:
                    skipped_canceled += 1
                    logger.debug(f"Skipping event with status '{event_status}': {event_data.get('Project', 'Unknown')}")
                    continue

                location = event_data.get('Location', '')
                if location:
                    locations.add(location)

                start_time = self._get_time_value(
                    event_data.get('Start Time') or
                    event_data.get('IN Time') or
                    event_data.get('StartTime') or
                    event_data.get('InTime')
                )
                end_time = self._get_time_value(
                    event_data.get('End Time') or
                    event_data.get('OUT Time') or
                    event_data.get('EndTime') or
                    event_data.get('OutTime')
                )

                event_name = (
                    event_data.get('Project') or
                    event_data.get('Text for Calendar') or
                    event_data.get('Description') or
                    event_data.get('Name') or
                    'Untitled Event'
                )

                is_all_day = False
                if not start_time and not end_time:
                    is_all_day = True
                    all_day_count += 1
                    event_date = event_data.get('Date', '')
                    if event_date:
                        try:
                            date_obj = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")
                        except:
                            date_obj = datetime.now()

                        in_time = date_obj.replace(hour=0, minute=0, second=0)
                        out_time = date_obj.replace(hour=23, minute=59, second=59)
                    else:
                        today = datetime.now()
                        in_time = today.replace(hour=0, minute=0, second=0)
                        out_time = today.replace(hour=23, minute=59, second=59)

                    logger.debug(f"All-day event: {event_name} at {location} (active 24 hours)")
                else:
                    in_time = self._parse_timestamp(start_time) if start_time else None
                    out_time = self._parse_timestamp(end_time) if end_time else None

                event_obj = {
                    'location': location,
                    'name': event_name,
                    'in_time': in_time.isoformat() if in_time else None,
                    'out_time': out_time.isoformat() if out_time else None,
                    'is_all_day': is_all_day,
                    'status': event_status,
                    'public_private': event_data.get('Public or Private', ''),
                    'ticketed': event_data.get('Ticketed?', ''),
                    'date': event_data.get('Date', ''),
                    'raw_data': event_data
                }

                events.append(event_obj)

            self.cached_events = events
            self.all_locations = self.all_locations.union(locations)

            SystemState.set('cached_events', events)
            SystemState.set('all_locations', list(self.all_locations))
            SystemState.set('last_api_poll', datetime.utcnow().isoformat())

            logger.info(f"Processed {len(events)} confirmed events from {len(locations)} locations")
            if all_day_count > 0:
                logger.info(f"  Including {all_day_count} all-day events (active 24 hours)")
            if skipped_canceled > 0:
                logger.info(f"  Skipped {skipped_canceled} canceled/released events")
            logger.debug(f"Locations discovered: {', '.join(sorted(locations))}")

        except Exception as e:
            logger.error(f"Error processing API response: {str(e)}", exc_info=True)

    def discover_all_locations(self):
        """
        Discover all locations by querying events from an extended date range.
        Also tries to query Location entity if it exists.
        """
        self.reload_settings()
        if not self.api_key:
            logger.warning("No API key configured. Skipping location discovery.")
            return []
        logger.info(f"Discovering locations from events in next {self.location_discovery_days} days...")

        discovered_locations = set()

        # Method 1: Try to get locations from a Location entity
        try:
            logger.debug("Checking for Location entity...")
            entity_names = self._get_entity_names()

            location_entities = [e for e in entity_names if 'location' in e.lower()]

            if location_entities:
                logger.info(f"Found location entities: {location_entities}")

                for entity_name in location_entities:
                    try:
                        payload = {
                            "xml": False,
                            "flatten": False,
                            "entities": [
                                {
                                    "entity": entity_name,
                                    "firstRowIndex": 0,
                                    "rowsCount": 1000,
                                    "columns": [],
                                    "filters": [],
                                    "orderby": [],
                                    "include": []
                                }
                            ]
                        }

                        data = self._make_api_request('getdata', method='POST', payload=payload)

                        if data and len(data) > 0:
                            rows = data[0].get('Rows', [])
                            logger.info(f"  {entity_name}: Found {len(rows)} location records")

                            for row in rows:
                                row_data = row.get('Data', {})
                                location_name = (
                                    row_data.get('Name') or
                                    row_data.get('LocationName') or
                                    row_data.get('Location') or
                                    row_data.get('Description')
                                )
                                if location_name:
                                    discovered_locations.add(location_name)
                    except Exception as e:
                        logger.debug(f"  Error querying {entity_name}: {e}")
            else:
                logger.debug("No Location entity found")
        except Exception as e:
            logger.debug(f"Error checking for Location entity: {e}")

        # Method 2: Get events from extended date range
        try:
            today = datetime.now().strftime("%m/%d/%Y")
            future = (datetime.now() + timedelta(days=self.location_discovery_days)).strftime("%m/%d/%Y")

            payload = {
                "xml": False,
                "flatten": False,
                "entities": [
                    {
                        "entity": "Event",
                        "firstRowIndex": 0,
                        "rowsCount": 1000,
                        "columns": ["Location"],
                        "filters": [
                            {
                                "field": "Date",
                                "operator": "GreaterOrEqual",
                                "value": today
                            },
                            {
                                "field": "Date",
                                "operator": "Less",
                                "value": future
                            }
                        ],
                        "orderby": [],
                        "include": []
                    }
                ]
            }

            data = self._make_api_request('getdata', method='POST', payload=payload)

            if data and len(data) > 0:
                rows = data[0].get('Rows', [])
                total_count = data[0].get('TotalCount', len(rows))

                logger.info(f"Found {len(rows)} events in next {self.location_discovery_days} days (total: {total_count})")

                for row in rows:
                    event_data = row.get('Data', {})
                    location = event_data.get('Location', '')
                    if location:
                        discovered_locations.add(location)

                logger.info(f"Discovered {len(discovered_locations)} unique locations from events")
        except Exception as e:
            logger.error(f"Error discovering locations from events: {e}")

        if discovered_locations:
            self.all_locations = discovered_locations
            SystemState.set('all_locations', list(discovered_locations))
            logger.info(f"Total locations discovered: {len(discovered_locations)}")
            logger.debug(f"Locations: {', '.join(sorted(discovered_locations))}")
        else:
            logger.warning("No locations discovered!")

        return list(discovered_locations)

    def discover_api_schema(self):
        """
        Discover API schema by fetching entity names and Event metadata.
        """
        self.reload_settings()
        if not self.api_key:
            logger.warning("No API key configured. Skipping schema discovery.")
            return [], []
        logger.info("Discovering ArtsVision API schema...")

        entity_names = self.get_entity_names()

        if entity_names:
            logger.info(f"Available entities: {', '.join(entity_names[:10])}{'...' if len(entity_names) > 10 else ''}")

        event_metadata = self.get_metadata('Event', fields_info=True)

        if event_metadata and len(event_metadata) > 0:
            fields = event_metadata[0].get('Fields', [])
            logger.info(f"Event entity discovered with {len(fields)} fields")

            field_info = {f['Name']: f['Type'] for f in fields}
            logger.debug(f"Event field mapping: {json.dumps(field_info, indent=2)}")

            key_fields = ['Start Time', 'End Time', 'IN Time', 'OUT Time',
                         'Location', 'Project', 'Event Status', 'Date',
                         'Public or Private', 'Ticketed?']

            found_fields = [f for f in key_fields if f in field_info]
            missing_fields = [f for f in key_fields if f not in field_info]

            if found_fields:
                logger.info(f"Found key fields: {', '.join(found_fields)}")
            if missing_fields:
                logger.warning(f"Missing expected fields: {', '.join(missing_fields)}")
                logger.info("Will try alternative field names during event processing")

        return entity_names, event_metadata

    def process_monitors(self):
        """Update all monitor states based on cached events"""
        try:
            self.reload_settings()
            monitors = Monitor.query.filter_by(enabled=True).all()
            logger.info(f"Processing {len(monitors)} monitors...")

            current_time = datetime.now()

            for monitor in monitors:
                self._update_monitor_state(monitor, current_time)

            db.session.commit()
            logger.info("Monitor processing complete")

        except Exception as e:
            logger.error(f"Error processing monitors: {str(e)}", exc_info=True)
            db.session.rollback()

    def _update_monitor_state(self, monitor, current_time):
        """Update a single monitor's state"""
        try:
            # Per-monitor overrides fall back to global settings when null
            pre_minutes = monitor.pre_show_minutes if monitor.pre_show_minutes is not None else self.pre_show_minutes
            post_minutes = monitor.post_show_minutes if monitor.post_show_minutes is not None else self.post_show_minutes

            location_events = [
                e for e in self.cached_events
                if e['location'] == monitor.location and e['in_time']
            ]

            if not location_events:
                monitor.is_active = False
                monitor.current_event = None
                monitor.next_event = None
                monitor.last_updated = datetime.now()
                return

            current_event = None
            next_events = []

            for event in location_events:
                in_time = datetime.fromisoformat(event['in_time'])

                activation_time = in_time - timedelta(minutes=pre_minutes)

                if event['out_time']:
                    out_time = datetime.fromisoformat(event['out_time'])
                    deactivation_time = out_time + timedelta(minutes=post_minutes)
                else:
                    deactivation_time = in_time + timedelta(hours=4)

                if activation_time <= current_time < deactivation_time:
                    current_event = {
                        'name': event['name'],
                        'in_time': event['in_time'],
                        'out_time': event['out_time'],
                        'is_all_day': event.get('is_all_day', False),
                        'activation_time': activation_time.isoformat(),
                        'deactivation_time': deactivation_time.isoformat()
                    }
                    break

                if current_time < activation_time:
                    next_events.append({
                        'name': event['name'],
                        'in_time': event['in_time'],
                        'out_time': event['out_time'],
                        'is_all_day': event.get('is_all_day', False),
                        'activation_time': activation_time.isoformat()
                    })

            next_events.sort(key=lambda x: x['activation_time'])

            was_active = monitor.is_active
            monitor.is_active = current_event is not None
            monitor.current_event = json.dumps(current_event) if current_event else None
            monitor.next_event = json.dumps(next_events[0]) if next_events else None
            monitor.last_updated = datetime.now()

            if monitor.webhook_enabled and was_active != monitor.is_active:
                self._trigger_webhook(monitor)

        except Exception as e:
            logger.error(f"Error updating monitor {monitor.id}: {str(e)}", exc_info=True)

    def generate_qsys_status_text(self, theaters, last_api_poll):
        """
        Generate a pre-formatted status text block for QSYS display controls.
        Mirrors the format from the Lua UpdateDisplay function.
        """
        lines = []
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        lines.append("=" * 40)
        lines.append(f"THEATER STATUS - Updated: {timestamp}")

        if last_api_poll:
            try:
                last_poll_dt = datetime.fromisoformat(last_api_poll)
                mins_ago = max(0, int((now - last_poll_dt).total_seconds() / 60))
                lines.append(
                    f"Last API Poll: {last_poll_dt.strftime('%Y-%m-%d %H:%M:%S')} ({mins_ago} min ago)"
                )
            except Exception:
                pass

        lines.append("=" * 40)
        lines.append("")

        current = [t for t in theaters if t['is_active'] and t.get('current_event')]
        if current:
            lines.append(f"CURRENT EVENTS ({len(current)}):")
            lines.append("")
            for i, t in enumerate(current, 1):
                ev = t['current_event']
                in_t = ev.get('in_time') or 'NO_IN'
                out_t = ev.get('out_time') or 'No OUT'
                deact = ev.get('deactivates_at') or '?'
                countdown = ev.get('deactivates_countdown') or '?'
                lines.append(f"{i}. {t['name']} - {ev['name']}")
                lines.append(f"   {in_t} - {out_t} | Inactive @ {deact} (in {countdown})")
                if i < len(current):
                    lines.append("")
        else:
            lines.append("CURRENT EVENTS: None")

        lines.append("")
        lines.append("=" * 40)
        lines.append("")

        upcoming = [t for t in theaters if not t['is_active'] and t.get('next_event')]
        upcoming.sort(key=lambda t: t['next_event'].get('activates_at') or '')

        if upcoming:
            lines.append(f"UPCOMING EVENTS ({len(upcoming)}):")
            lines.append("")
            for i, t in enumerate(upcoming, 1):
                ev = t['next_event']
                in_t = ev.get('in_time') or 'NO_IN'
                out_t = ev.get('out_time') or 'No OUT'
                act = ev.get('activates_at') or '?'
                countdown = ev.get('activates_countdown') or '?'
                lines.append(f"{i}. {t['name']} - {ev['name']}")
                lines.append(f"   {in_t} - {out_t} | Active @ {act} (in {countdown})")
                if i < len(upcoming):
                    lines.append("")
        else:
            lines.append("UPCOMING EVENTS: None")

        lines.append("")
        lines.append("=" * 40)

        return "\n".join(lines)

    def _trigger_webhook(self, monitor):
        """Trigger webhook for monitor state change"""
        try:
            if not monitor.webhook_url:
                return

            logger.info(f"Triggering webhook for monitor {monitor.id} ({monitor.name})")

            webhook_data = {
                'monitor_id': monitor.id,
                'monitor_name': monitor.name,
                'location': monitor.location,
                'is_active': monitor.is_active,
                'current_event': json.loads(monitor.current_event) if monitor.current_event else None,
                'next_event': json.loads(monitor.next_event) if monitor.next_event else None,
                'timestamp': datetime.utcnow().isoformat()
            }

            headers = monitor.get_webhook_headers()

            if monitor.webhook_method.upper() == 'POST':
                if monitor.webhook_body_template:
                    body = self._render_template(monitor.webhook_body_template, webhook_data)
                    response = requests.post(
                        monitor.webhook_url,
                        data=body,
                        headers=headers,
                        timeout=10
                    )
                else:
                    response = requests.post(
                        monitor.webhook_url,
                        json=webhook_data,
                        headers=headers,
                        timeout=10
                    )
            else:  # GET
                response = requests.get(
                    monitor.webhook_url,
                    params=webhook_data,
                    headers=headers,
                    timeout=10
                )

            logger.info(f"Webhook response: {response.status_code}")

        except Exception as e:
            logger.error(f"Error triggering webhook for monitor {monitor.id}: {str(e)}", exc_info=True)

    def _render_template(self, template, data):
        """Simple template rendering using string format"""
        try:
            return template.format(**data)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template

    def _get_time_value(self, value):
        """Extract time string from various value types"""
        if value is None:
            return None
        if isinstance(value, str) and value:
            return value
        return None

    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime"""
        if not timestamp_str or not isinstance(timestamp_str, str):
            return None

        try:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)

                    # If year is 1900, use today's date
                    if dt.year == 1900:
                        today = datetime.now()
                        dt = dt.replace(year=today.year, month=today.month, day=today.day)

                    return dt
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error parsing timestamp '{timestamp_str}': {str(e)}")
            return None

    def get_all_locations(self):
        """Get all discovered locations"""
        return sorted(list(self.all_locations))

import requests
import logging
from datetime import datetime, timedelta
from models import db, Monitor, SystemState
import json
import urllib3

logger = logging.getLogger(__name__)


class ArtsVisionPoller:
    """Poll ArtsVision API and process events"""
    
    def __init__(self, api_key, api_url, pre_show_minutes=30, post_show_minutes=60, verify_ssl=True, filter_confirmed_only=True, location_discovery_days=90):
        self.api_key = api_key
        # Extract base URL from api_url (remove /getdata if present)
        base_url = api_url.replace('/getdata', '').rstrip('/')
        self.api_base_url = base_url
        self.api_url = api_url
        self.pre_show_minutes = pre_show_minutes
        self.post_show_minutes = post_show_minutes
        self.verify_ssl = verify_ssl
        self.filter_confirmed_only = filter_confirmed_only
        self.location_discovery_days = location_discovery_days
        self.cached_events = []
        self.all_locations = set()
        self.event_metadata = None
        
        # Warn if SSL verification is disabled
        if not self.verify_ssl:
            logger.warning("=" * 70)
            logger.warning("SSL CERTIFICATE VERIFICATION IS DISABLED")
            logger.warning("This is INSECURE and should only be used for testing")
            logger.warning("with self-signed certificates on trusted networks!")
            logger.warning("=" * 70)
            # Suppress the InsecureRequestWarning
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
            # Cache for reference
            SystemState.set('available_entities', entity_names)
        
        return entity_names or []
    
    def get_metadata(self, entity_name=None, fields_info=True):
        """
        Get metadata for entities including field definitions.
        Endpoint: GET /api/getmetadata?startWithEntity=X&fieldsInfo=true
        
        Args:
            entity_name: Optional entity to start from (e.g., "Event")
            fields_info: Whether to include field definitions
        
        Returns: List of ApiMetaEntity objects with structure:
            {
                "Entity": "Event",
                "AllowIndividualUpdate": true,
                "Fields": [
                    {"Name": "fieldname", "Type": "string/int/bool/date/number"}
                ],
                "Entities": [...child entities...]
            }
        """
        logger.info(f"Fetching metadata for entity: {entity_name or 'all'}")
        
        # Build query parameters
        params = []
        if entity_name:
            params.append(f"startWithEntity={entity_name}")
        params.append(f"fieldsInfo={'true' if fields_info else 'false'}")
        
        endpoint = f"getmetadata?{'&'.join(params)}" if params else 'getmetadata'
        metadata = self._make_api_request(endpoint, method='GET')
        
        if metadata and entity_name == 'Event':
            # Cache Event metadata for field mapping
            self.event_metadata = metadata
            SystemState.set('event_metadata', metadata)
            
            # Log available fields for debugging
            if metadata and len(metadata) > 0:
                fields = metadata[0].get('Fields', [])
                field_names = [f['Name'] for f in fields]
                logger.info(f"Event entity has {len(field_names)} fields")
                logger.debug(f"Available Event fields: {', '.join(field_names)}")
        
        return metadata or []
    
    def poll_api(self):
        """Fetch events from ArtsVision API"""
        try:
            logger.info("Polling ArtsVision API...")
            
            today = datetime.now().strftime("%m/%d/%Y")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
            
            # Build filters
            filters = [
                {
                    "field": "Date",
                    "operator": "GreaterOrEqual",
                    "value": today
                },
                {
                    "field": "Date",
                    "operator": "Less",
                    "value": tomorrow
                }
            ]
            
            # Add status filter if configured
            if self.filter_confirmed_only:
                filters.append({
                    "field": "Event Status",
                    "operator": "Equal",
                    "value": "Confirmed"
                })
            
            # Build request payload
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
            
            # Use the new _make_api_request method which handles Status/Data wrapper
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
            # data is already the Data array from {"Status": 0, "Data": [...]}
            if not data or len(data) == 0:
                logger.warning("No data in API response")
                return
            
            # Get the first entity (should be Event entity)
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
                
                # Check event status - skip if not confirmed
                event_status = event_data.get('Event Status', '')
                if event_status and event_status.lower() in ['canceled', 'cancelled', 'released', 'tentative']:
                    skipped_canceled += 1
                    logger.debug(f"Skipping event with status '{event_status}': {event_data.get('Project', 'Unknown')}")
                    continue
                
                # Extract location
                location = event_data.get('Location', '')
                if location:
                    locations.add(location)
                
                # Get event times - try multiple possible field names
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
                
                # Get event name - try multiple field names
                event_name = (
                    event_data.get('Project') or 
                    event_data.get('Text for Calendar') or
                    event_data.get('Description') or
                    event_data.get('Name') or
                    'Untitled Event'
                )
                
                # Handle all-day events (no specific times)
                is_all_day = False
                if not start_time and not end_time:
                    is_all_day = True
                    all_day_count += 1
                    # Set to full day (midnight to midnight)
                    event_date = event_data.get('Date', '')
                    if event_date:
                        # Parse the date and create full day times
                        try:
                            date_obj = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")
                        except:
                            date_obj = datetime.now()
                        
                        # All-day: 12:00 AM to 11:59 PM
                        in_time = date_obj.replace(hour=0, minute=0, second=0)
                        out_time = date_obj.replace(hour=23, minute=59, second=59)
                    else:
                        # Fallback to today if no date
                        today = datetime.now()
                        in_time = today.replace(hour=0, minute=0, second=0)
                        out_time = today.replace(hour=23, minute=59, second=59)
                    
                    logger.debug(f"All-day event: {event_name} at {location} (active 24 hours)")
                else:
                    # Regular event with specific times
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
            
            # Cache the events
            self.cached_events = events
            
            # Merge new locations with existing ones (preserve locations from extended discovery)
            self.all_locations = self.all_locations.union(locations)
            
            # Store in database
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
        logger.info(f"Discovering locations from events in next {self.location_discovery_days} days...")
        
        discovered_locations = set()
        
        # Method 1: Try to get locations from a Location entity
        try:
            logger.debug("Checking for Location entity...")
            entity_names = self._get_entity_names()
            
            # Look for any entity with 'location' in the name
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
                            
                            # Try to extract location names from different possible field names
                            for row in rows:
                                row_data = row.get('Data', {})
                                # Try common field names for location name
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
                        "rowsCount": 1000,  # Get up to 1000 events
                        "columns": ["Location"],  # Only get Location field for efficiency
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
        
        # Store discovered locations
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
        This helps understand available entities and fields.
        Should be called once during initialization.
        """
        logger.info("Discovering ArtsVision API schema...")
        
        # Get all available entities
        entity_names = self.get_entity_names()
        
        if entity_names:
            logger.info(f"Available entities: {', '.join(entity_names[:10])}{'...' if len(entity_names) > 10 else ''}")
        
        # Get metadata for Event entity specifically
        event_metadata = self.get_metadata('Event', fields_info=True)
        
        if event_metadata and len(event_metadata) > 0:
            fields = event_metadata[0].get('Fields', [])
            logger.info(f"Event entity discovered with {len(fields)} fields")
            
            # Log field names and types for debugging
            field_info = {f['Name']: f['Type'] for f in fields}
            logger.debug(f"Event field mapping: {json.dumps(field_info, indent=2)}")
            
            # Look for our key fields
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
            monitors = Monitor.query.filter_by(enabled=True).all()
            logger.info(f"Processing {len(monitors)} monitors...")
            
            current_time = datetime.utcnow()
            
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
            # Get events for this monitor's location
            location_events = [
                e for e in self.cached_events 
                if e['location'] == monitor.location and e['in_time']
            ]
            
            if not location_events:
                monitor.is_active = False
                monitor.current_event = None
                monitor.next_event = None
                monitor.last_updated = datetime.utcnow()
                return
            
            # Find current and next events
            current_event = None
            next_events = []
            
            for event in location_events:
                in_time = datetime.fromisoformat(event['in_time'])
                
                # Calculate activation/deactivation times
                activation_time = in_time - timedelta(minutes=self.pre_show_minutes)
                
                if event['out_time']:
                    out_time = datetime.fromisoformat(event['out_time'])
                    deactivation_time = out_time + timedelta(minutes=self.post_show_minutes)
                else:
                    # No end time, keep active for 4 hours
                    deactivation_time = in_time + timedelta(hours=4)
                
                # Check if currently active
                if activation_time <= current_time < deactivation_time:
                    current_event = {
                        'name': event['name'],
                        'in_time': event['in_time'],
                        'out_time': event['out_time'],
                        'activation_time': activation_time.isoformat(),
                        'deactivation_time': deactivation_time.isoformat()
                    }
                    break
                
                # Collect upcoming events
                if current_time < activation_time:
                    next_events.append({
                        'name': event['name'],
                        'in_time': event['in_time'],
                        'out_time': event['out_time'],
                        'activation_time': activation_time.isoformat()
                    })
            
            # Sort upcoming events by activation time
            next_events.sort(key=lambda x: x['activation_time'])
            
            # Update monitor
            was_active = monitor.is_active
            monitor.is_active = current_event is not None
            monitor.current_event = json.dumps(current_event) if current_event else None
            monitor.next_event = json.dumps(next_events[0]) if next_events else None
            monitor.last_updated = datetime.utcnow()
            
            # Trigger webhook if state changed
            if monitor.webhook_enabled and was_active != monitor.is_active:
                self._trigger_webhook(monitor)
                
        except Exception as e:
            logger.error(f"Error updating monitor {monitor.id}: {str(e)}", exc_info=True)
    
    def _trigger_webhook(self, monitor):
        """Trigger webhook for monitor state change"""
        try:
            if not monitor.webhook_url:
                return
            
            logger.info(f"Triggering webhook for monitor {monitor.id} ({monitor.name})")
            
            # Prepare data
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
                # Use template if provided, otherwise send JSON
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
            # Try parsing formats like "2026-02-03 19:30:00" or "2026-02-03T19:30:00"
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

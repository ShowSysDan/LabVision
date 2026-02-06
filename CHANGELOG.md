# Changelog

## Version 1.1.0 - Enhanced API Integration (2026-02-06)

### 🎯 Major Improvements

#### **SSL Certificate Support**
- **NEW**: `ARTSVISION_VERIFY_SSL` configuration option
  - Handles self-signed SSL certificates
  - Common in corporate/enterprise ArtsVision deployments
  - Set to `false` in `.env` to bypass certificate verification
  - Includes security warnings when disabled
  - See `SSL_CERTIFICATE_FIX.md` for detailed instructions

#### **Complete API Documentation Integration**
- Integrated full ArtsVision API documentation
- Implemented proper API response handling with Status/Data wrapper
- All responses now properly checked for Status codes (0=success, 3=error)

#### **Dynamic Schema Discovery**
- **NEW**: `GetEntityNames` endpoint integration
  - Discovers all available entities from ArtsVision
  - Cached for reference and debugging
  
- **NEW**: `GetMetadata` endpoint integration
  - Fetches Event entity field definitions on startup
  - Discovers field names and types automatically
  - Adapts to API changes without code modifications
  
- **NEW**: `/api/schema` endpoint
  - View discovered entities and fields
  - Useful for debugging field mapping issues
  - Shows exact field names used by your ArtsVision instance

#### **Improved Field Mapping**
- Extended field name detection with fallbacks:
  - Start times: `Start Time`, `IN Time`, `StartTime`, `InTime`
  - End times: `End Time`, `OUT Time`, `EndTime`, `OutTime`
  - Event names: `Project`, `Text for Calendar`, `Description`, `Name`
- Better logging of field discovery
- Warning messages for missing expected fields

#### **Enhanced Error Handling**
- Centralized API request method (`_make_api_request`)
- Proper handling of HTTP errors vs API errors
- More detailed error logging
- Graceful degradation if schema discovery fails

#### **Better Logging**
- DEBUG level logs for field mapping
- INFO level logs for schema discovery
- Detailed logging of available fields
- Warning messages for field mismatches

### 🐛 Bug Fixes
- Fixed response parsing to work with Status/Data wrapper
- Improved handling of missing fields
- Better error messages for API failures

### 📚 Documentation Updates
- Added schema discovery section to README
- Enhanced troubleshooting guide
- Added field mapping troubleshooting steps
- Documented new `/api/schema` endpoint

### 🔄 API Changes
- Base URL handling improved (automatically strips `/getdata`)
- API key always sent in header (recommended by documentation)
- Consistent timeout handling (30 seconds)

### 🚀 Performance
- Schema discovery runs once on startup (cached)
- No performance impact on regular polling
- Metadata cached in database for reference

---

## Version 1.0.0 - Initial Release (2026-02-06)

### Features
- Web-based dashboard for monitoring ArtsVision events
- Multi-location support with auto-discovery
- Real-time WebSocket updates
- Webhook integration (HTTP POST/GET)
- SQLite database for persistence
- Responsive design for mobile devices
- Background scheduling for API polling
- Monitor management (create, edit, delete)
- Event countdown timers
- Pre-show and post-show activation windows

### Architecture
- Flask web framework
- Flask-SocketIO for real-time updates
- APScheduler for background tasks
- SQLAlchemy ORM for database
- Modern vanilla JavaScript frontend

---

## Upgrade Notes

### From 1.0.0 to 1.1.0

**No breaking changes!** Just update your files:

```bash
# Backup your database
cp artsvision_monitors.db artsvision_monitors.db.backup

# Extract new version over existing
tar -xzf artsvision-monitor.tar.gz

# Restart the application
# Your database and .env will be preserved
```

**New Features Available:**
1. Visit `/api/schema` to see discovered API schema
2. Check logs for field mapping information
3. Schema discovery runs automatically on startup

**Recommendations:**
- Check logs on first startup to see discovered fields
- Visit `/api/schema` to verify field names match your expectations
- Review troubleshooting section if events aren't detected

---

## Future Roadmap

### Planned Features
- [ ] Email notifications
- [ ] Calendar view
- [ ] Historical event logging
- [ ] Analytics dashboard
- [ ] Multi-day event view
- [ ] Advanced filtering UI
- [ ] User authentication
- [ ] Role-based access control
- [ ] Export/import monitor configs
- [ ] Custom field mapping UI

### Under Consideration
- [ ] Mobile app
- [ ] SMS notifications
- [ ] Integration templates
- [ ] Event templates
- [ ] Conflict detection
- [ ] Resource scheduling
- [ ] Reporting engine

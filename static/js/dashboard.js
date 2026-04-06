// Global state
let monitors = [];
let locations = [];
let socket = null;
let currentEditingId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSocketIO();
    loadLocations();
    loadMonitors();
    setupEventListeners();
});

// ============================================================================
// WebSocket / SocketIO
// ============================================================================

function initSocketIO() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });
    
    socket.on('monitors_update', function(data) {
        console.log('Monitors update received', data);
        monitors = data.monitors;
        renderMonitors();
        updateLastUpdate();
    });
    
    socket.on('monitor_created', function(monitor) {
        console.log('Monitor created', monitor);
        loadMonitors();
    });
    
    socket.on('monitor_updated', function(monitor) {
        console.log('Monitor updated', monitor);
        loadMonitors();
    });
    
    socket.on('monitor_deleted', function(data) {
        console.log('Monitor deleted', data);
        loadMonitors();
    });
}

function updateConnectionStatus(connected) {
    // Could add a connection indicator in the UI
    if (!connected) {
        console.warn('Lost connection to server');
    }
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Add Monitor button
    document.getElementById('addMonitorBtn').addEventListener('click', function() {
        openMonitorModal();
    });
    
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        manualRefresh();
    });
    
    // Monitor modal close (X button inside the monitor modal)
    document.querySelector('#monitorModal .close').addEventListener('click', function() {
        closeMonitorModal();
    });

    // Cancel button
    document.getElementById('cancelBtn').addEventListener('click', function() {
        closeMonitorModal();
    });

    // Settings button
    document.getElementById('settingsBtn').addEventListener('click', function() {
        openSettingsModal();
    });

    // Settings modal close
    document.getElementById('settingsClose').addEventListener('click', function() {
        closeSettingsModal();
    });

    // Settings cancel button
    document.getElementById('settingsCancelBtn').addEventListener('click', function() {
        closeSettingsModal();
    });

    // Settings form submit
    document.getElementById('settingsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
    
    // Syslog enabled checkbox
    document.getElementById('settingSyslogEnabled').addEventListener('change', function() {
        toggleSyslogSettings(this.checked);
    });

    // Webhook enabled checkbox
    document.getElementById('webhookEnabled').addEventListener('change', function() {
        toggleWebhookSettings(this.checked);
    });

    // Display enabled checkbox
    document.getElementById('displayEnabled').addEventListener('change', function() {
        toggleDisplaySettings(this.checked);
    });
    
    // Form submit
    document.getElementById('monitorForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveMonitor();
    });
    
    // Click outside modal to close
    window.addEventListener('click', function(e) {
        const monitorModal = document.getElementById('monitorModal');
        const settingsModal = document.getElementById('settingsModal');
        if (e.target === monitorModal) {
            closeMonitorModal();
        }
        if (e.target === settingsModal) {
            closeSettingsModal();
        }
    });
}

// ============================================================================
// API Calls
// ============================================================================

async function loadMonitors() {
    try {
        const response = await fetch('/api/monitors');
        const data = await response.json();
        monitors = data.monitors;
        renderMonitors();
        updateLastUpdate();
    } catch (error) {
        console.error('Error loading monitors:', error);
    }
}

async function loadLocations() {
    try {
        const response = await fetch('/api/locations');
        const data = await response.json();
        locations = data.locations;
        populateLocationDropdown();
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

async function saveMonitor() {
    const id = document.getElementById('monitorId').value;
    const name = document.getElementById('monitorName').value;
    const location = document.getElementById('monitorLocation').value;
    const webhookEnabled = document.getElementById('webhookEnabled').checked;
    const webhookUrl = document.getElementById('webhookUrl').value;
    const webhookMethod = document.getElementById('webhookMethod').value;
    const webhookHeaders = document.getElementById('webhookHeaders').value;
    const webhookBodyTemplate = document.getElementById('webhookBodyTemplate').value;
    
    // Validate webhook headers if provided
    let parsedHeaders = {};
    if (webhookHeaders.trim()) {
        try {
            parsedHeaders = JSON.parse(webhookHeaders);
        } catch (e) {
            alert('Invalid JSON in webhook headers');
            return;
        }
    }
    
    const displayEnabled = document.getElementById('displayEnabled').checked;
    const noEventText = document.getElementById('noEventText').value;
    const showCountdown = document.getElementById('showCountdown').checked;

    const qsysControlName = document.getElementById('qsysControlName').value.trim();
    const preShowMinutes = document.getElementById('preShowMinutes').value;
    const postShowMinutes = document.getElementById('postShowMinutes').value;

    const data = {
        name,
        location,
        webhook_enabled: webhookEnabled,
        webhook_url: webhookUrl || null,
        webhook_method: webhookMethod,
        webhook_headers: parsedHeaders,
        webhook_body_template: webhookBodyTemplate || null,
        display_enabled: displayEnabled,
        no_event_text: noEventText || 'No Event',
        show_countdown: showCountdown,
        qsys_control_name: qsysControlName || null,
        pre_show_minutes: preShowMinutes !== '' ? parseInt(preShowMinutes) : null,
        post_show_minutes: postShowMinutes !== '' ? parseInt(postShowMinutes) : null,
    };
    
    try {
        let response;
        if (id) {
            // Update existing monitor
            response = await fetch(`/api/monitors/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        } else {
            // Create new monitor
            response = await fetch('/api/monitors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            closeMonitorModal();
            loadMonitors();
        } else {
            const error = await response.json();
            alert('Error saving monitor: ' + error.error);
        }
    } catch (error) {
        console.error('Error saving monitor:', error);
        alert('Error saving monitor: ' + error.message);
    }
}

async function deleteMonitor(id) {
    if (!confirm('Are you sure you want to delete this monitor?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/monitors/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadMonitors();
        } else {
            alert('Error deleting monitor');
        }
    } catch (error) {
        console.error('Error deleting monitor:', error);
        alert('Error deleting monitor: ' + error.message);
    }
}

async function testWebhook(id) {
    try {
        const response = await fetch(`/api/test-webhook/${id}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Webhook triggered successfully!');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error testing webhook:', error);
        alert('Error testing webhook: ' + error.message);
    }
}

async function manualRefresh() {
    const btn = document.getElementById('refreshBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Refreshing...';
    
    try {
        const response = await fetch('/api/refresh', {
            method: 'POST'
        });
        
        if (response.ok) {
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = '🔄 Refresh Now';
            }, 2000);
        }
    } catch (error) {
        console.error('Error refreshing:', error);
        btn.disabled = false;
        btn.textContent = '🔄 Refresh Now';
    }
}

// ============================================================================
// UI Rendering
// ============================================================================

function renderMonitors() {
    const container = document.getElementById('monitorsContainer');
    const emptyState = document.getElementById('noMonitors');
    
    if (monitors.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    emptyState.style.display = 'none';
    
    container.innerHTML = monitors.map(monitor => createMonitorCard(monitor)).join('');
}

function createMonitorCard(monitor) {
    const isActive = monitor.is_active;
    const statusClass = isActive ? 'active' : 'inactive';
    const statusText = isActive ? 'ACTIVE' : 'Inactive';
    
    let currentEventHtml = '<p class="no-event">No current event</p>';
    if (monitor.current_event) {
        const event = monitor.current_event;
        
        let eventTimeHtml;
        if (event.is_all_day) {
            eventTimeHtml = '<div class="event-time"><strong>All-Day Event</strong></div>';
        } else {
            const inTime = formatTime(event.in_time);
            const outTime = event.out_time ? formatTime(event.out_time) : 'No end time';
            eventTimeHtml = `<div class="event-time">${inTime} - ${outTime}</div>`;
        }
        
        const deactivationTime = formatTime(event.deactivation_time);
        const countdown = getCountdown(event.deactivation_time);
        
        currentEventHtml = `
            <div class="event-info">
                <div class="event-name">${escapeHtml(event.name)}</div>
                ${eventTimeHtml}
                <div class="event-countdown">Deactivates at ${deactivationTime} (${countdown})</div>
            </div>
        `;
    }
    
    let nextEventHtml = '<p class="no-event">No upcoming events</p>';
    if (monitor.next_event) {
        const event = monitor.next_event;
        
        let eventTimeHtml;
        if (event.is_all_day) {
            eventTimeHtml = '<div class="event-time"><strong>All-Day Event</strong></div>';
        } else {
            const inTime = formatTime(event.in_time);
            const outTime = event.out_time ? formatTime(event.out_time) : 'No end time';
            eventTimeHtml = `<div class="event-time">${inTime} - ${outTime}</div>`;
        }
        
        const activationTime = formatTime(event.activation_time);
        const countdown = getCountdown(event.activation_time);
        
        nextEventHtml = `
            <div class="event-info">
                <div class="event-name">${escapeHtml(event.name)}</div>
                ${eventTimeHtml}
                <div class="event-countdown">Activates at ${activationTime} (${countdown})</div>
            </div>
        `;
    }
    
    const webhookBadge = monitor.webhook_enabled ?
        '<span class="webhook-badge">🔗 Webhook Enabled</span>' : '';

    const qsysBadge = monitor.qsys_control_name ?
        `<span class="webhook-badge">⚙️ QSYS: ${escapeHtml(monitor.qsys_control_name)}</span>` : '';

    const displaySlug = monitor.display_slug || monitor.name.toLowerCase().replace(/ /g, '-');
    const displayLink = monitor.display_enabled ?
        `<div class="display-link-section">
            <span class="display-badge">📺 TV Display</span>
            <a href="/display/${escapeHtml(displaySlug)}" target="_blank" class="display-url">/display/${escapeHtml(displaySlug)}</a>
        </div>` : '';

    return `
        <div class="monitor-card" data-id="${monitor.id}">
            <div class="monitor-header">
                <div class="monitor-title">
                    <h3>${escapeHtml(monitor.name)}</h3>
                    <div class="monitor-location">📍 ${escapeHtml(monitor.location)}</div>
                </div>
                <div class="monitor-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editMonitor(${monitor.id})">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteMonitor(${monitor.id})">🗑️</button>
                </div>
            </div>
            <div class="monitor-body">
                <div class="status-indicator ${statusClass}">
                    <span class="status-dot ${statusClass}"></span>
                    <span>${statusText}</span>
                </div>

                <div class="event-section">
                    <h4>Current Event</h4>
                    ${currentEventHtml}
                </div>

                <div class="event-section">
                    <h4>Next Event</h4>
                    ${nextEventHtml}
                </div>

                ${webhookBadge}
                ${qsysBadge}
                ${monitor.webhook_enabled ?
                    `<button class="btn btn-sm btn-secondary" style="margin-top: 0.5rem;" onclick="testWebhook(${monitor.id})">Test Webhook</button>` :
                    ''}
                ${displayLink}
            </div>
        </div>
    `;
}

function populateLocationDropdown() {
    const select = document.getElementById('monitorLocation');
    select.innerHTML = '<option value="">Select a location...</option>' +
        locations.map(loc => `<option value="${escapeHtml(loc)}">${escapeHtml(loc)}</option>`).join('');
}

// ============================================================================
// Modal Management
// ============================================================================

function openMonitorModal(monitor = null) {
    const modal = document.getElementById('monitorModal');
    const form = document.getElementById('monitorForm');
    
    form.reset();
    
    if (monitor) {
        // Edit mode
        document.getElementById('modalTitle').textContent = 'Edit Monitor';
        document.getElementById('monitorId').value = monitor.id;
        document.getElementById('monitorName').value = monitor.name;
        document.getElementById('monitorLocation').value = monitor.location;
        document.getElementById('webhookEnabled').checked = monitor.webhook_enabled;
        document.getElementById('webhookUrl').value = monitor.webhook_url || '';
        document.getElementById('webhookMethod').value = monitor.webhook_method || 'POST';
        document.getElementById('webhookHeaders').value =
            monitor.webhook_headers ? JSON.stringify(monitor.webhook_headers, null, 2) : '';
        document.getElementById('webhookBodyTemplate').value = monitor.webhook_body_template || '';
        document.getElementById('displayEnabled').checked = monitor.display_enabled || false;
        document.getElementById('noEventText').value = monitor.no_event_text || '';
        document.getElementById('showCountdown').checked = monitor.show_countdown !== false;
        document.getElementById('qsysControlName').value = monitor.qsys_control_name || '';
        document.getElementById('preShowMinutes').value = monitor.pre_show_minutes != null ? monitor.pre_show_minutes : '';
        document.getElementById('postShowMinutes').value = monitor.post_show_minutes != null ? monitor.post_show_minutes : '';

        toggleWebhookSettings(monitor.webhook_enabled);
        toggleDisplaySettings(monitor.display_enabled || false);
    } else {
        // Add mode
        document.getElementById('modalTitle').textContent = 'Add Monitor';
        document.getElementById('monitorId').value = '';
        toggleWebhookSettings(false);
        toggleDisplaySettings(false);
    }
    
    modal.classList.add('show');
}

function closeMonitorModal() {
    const modal = document.getElementById('monitorModal');
    modal.classList.remove('show');
}

function editMonitor(id) {
    const monitor = monitors.find(m => m.id === id);
    if (monitor) {
        openMonitorModal(monitor);
    }
}

function toggleWebhookSettings(enabled) {
    const settings = document.getElementById('webhookSettings');
    settings.style.display = enabled ? 'block' : 'none';
}

function toggleDisplaySettings(enabled) {
    const settings = document.getElementById('displaySettings');
    settings.style.display = enabled ? 'block' : 'none';
}

function toggleSyslogSettings(enabled) {
    document.getElementById('syslogSettings').style.display = enabled ? 'block' : 'none';
}

// ============================================================================
// Settings Management
// ============================================================================

async function openSettingsModal() {
    const modal = document.getElementById('settingsModal');

    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();

        // Populate form fields
        document.getElementById('settingApiKey').value = '';
        document.getElementById('settingApiKey').placeholder = settings.api_key_masked || 'Enter your ArtsVision API key';
        document.getElementById('apiKeyHint').textContent = settings.api_key_masked ?
            'Current key: ' + settings.api_key_masked + ' (leave blank to keep current)' :
            'No API key set - enter one to connect to ArtsVision';
        document.getElementById('settingApiUrl').value = settings.api_url || '';
        document.getElementById('settingVerifySsl').checked = settings.verify_ssl !== false;
        document.getElementById('settingApiPollInterval').value = settings.api_poll_interval || 1800;
        document.getElementById('settingProcessInterval').value = settings.process_interval || 60;
        document.getElementById('settingPreShowMinutes').value = settings.pre_show_minutes || 30;
        document.getElementById('settingPostShowMinutes').value = settings.post_show_minutes || 60;
        document.getElementById('settingFilterConfirmed').checked = settings.filter_confirmed_only !== false;
        document.getElementById('settingDiscoveryDays').value = settings.location_discovery_days || 90;

        const syslogEnabled = settings.syslog_enabled || false;
        document.getElementById('settingSyslogEnabled').checked = syslogEnabled;
        document.getElementById('settingSyslogHost').value = settings.syslog_host || '';
        document.getElementById('settingSyslogPort').value = settings.syslog_port || 514;
        toggleSyslogSettings(syslogEnabled);

    } catch (error) {
        console.error('Error loading settings:', error);
    }

    modal.classList.add('show');
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('show');
}

async function saveSettings() {
    const apiKey = document.getElementById('settingApiKey').value;
    const data = {
        api_url: document.getElementById('settingApiUrl').value,
        verify_ssl: document.getElementById('settingVerifySsl').checked,
        api_poll_interval: parseInt(document.getElementById('settingApiPollInterval').value) || 1800,
        process_interval: parseInt(document.getElementById('settingProcessInterval').value) || 60,
        pre_show_minutes: parseInt(document.getElementById('settingPreShowMinutes').value) || 30,
        post_show_minutes: parseInt(document.getElementById('settingPostShowMinutes').value) || 60,
        filter_confirmed_only: document.getElementById('settingFilterConfirmed').checked,
        location_discovery_days: parseInt(document.getElementById('settingDiscoveryDays').value) || 90
    };

    data.syslog_enabled = document.getElementById('settingSyslogEnabled').checked;
    data.syslog_host = document.getElementById('settingSyslogHost').value.trim();
    data.syslog_port = parseInt(document.getElementById('settingSyslogPort').value) || 514;

    // Only send api_key if the user typed a new one
    if (apiKey && !apiKey.startsWith('*')) {
        data.api_key = apiKey;
    }

    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeSettingsModal();
            alert('Settings saved! Changes will take effect on the next poll cycle.');
        } else {
            const error = await response.json();
            alert('Error saving settings: ' + (error.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Error saving settings: ' + error.message);
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatTime(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
    });
}

function getCountdown(isoString) {
    if (!isoString) return 'N/A';
    
    const target = new Date(isoString);
    const now = new Date();
    const diff = target - now;
    
    if (diff < 0) return 'Past';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function updateLastUpdate() {
    const element = document.getElementById('lastUpdate');
    const now = new Date();
    element.textContent = `Last update: ${now.toLocaleTimeString()}`;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Update countdowns every minute
setInterval(() => {
    renderMonitors();
}, 60000);

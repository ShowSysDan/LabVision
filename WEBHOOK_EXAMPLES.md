# Webhook Integration Examples

This document provides real-world examples of how to configure webhooks to integrate the ArtsVision Monitor with various systems.

## Table of Contents
- [Basic Examples](#basic-examples)
- [Q-SYS Control](#q-sys-control)
- [Crestron/Extron](#crestronextron)
- [Slack Notifications](#slack-notifications)
- [Microsoft Teams](#microsoft-teams)
- [Discord](#discord)
- [Home Assistant](#home-assistant)
- [Custom HTTP API](#custom-http-api)

---

## Basic Examples

### Simple POST Request

**Use Case**: Send JSON data to a custom API

**Configuration**:
- Method: `POST`
- URL: `https://your-api.com/theater/status`
- Headers:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer your-token-here"
}
```
- Body Template:
```json
{
  "location": "{location}",
  "is_active": {is_active},
  "monitor_name": "{monitor_name}",
  "timestamp": "{timestamp}"
}
```

### Simple GET Request

**Use Case**: Trigger a webhook that doesn't need detailed data

**Configuration**:
- Method: `GET`
- URL: `https://your-system.com/trigger?location={location}&active={is_active}`
- Headers: (none needed)

---

## Q-SYS Control

Q-SYS can receive HTTP commands to trigger Named Controls.

### Method 1: Using Q-SYS Web Server API

**Configuration**:
- Method: `POST`
- URL: `http://qsys-core-ip/api/v0/cores/self/controls/set`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "Name": "Theater.{location}.Active",
  "Value": {is_active}
}
```

---

## Crestron/Extron

### Crestron HTTP Feedback

**Configuration**:
- Method: `GET`
- URL: `http://processor-ip/api/command?cmd=setTheaterStatus&location={location}&status={is_active}`

### Extron Simple Window

**Configuration**:
- Method: `POST`
- URL: `http://processor-ip:80`
- Headers:
```json
{
  "Content-Type": "text/plain"
}
```
- Body Template:
```
W{location}CVS{is_active}
```

---

## Slack Notifications

Send notifications to a Slack channel.

### Step 1: Create Slack Webhook
1. Go to https://api.slack.com/messaging/webhooks
2. Create an Incoming Webhook for your workspace
3. Copy the webhook URL (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

### Step 2: Configure Monitor Webhook

**Configuration**:
- Method: `POST`
- URL: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "text": "🎭 *{monitor_name}* status changed",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Location:* {location}\n*Status:* {is_active}\n*Time:* {timestamp}"
      }
    }
  ]
}
```

---

## Microsoft Teams

Send notifications to Microsoft Teams channel.

### Step 1: Create Teams Webhook
1. In Teams, go to the channel where you want notifications
2. Click "..." → "Connectors" → "Incoming Webhook"
3. Configure and copy the webhook URL

### Step 2: Configure Monitor Webhook

**Configuration**:
- Method: `POST`
- URL: `https://outlook.office.com/webhook/YOUR-WEBHOOK-URL`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "0076D7",
  "summary": "Theater Status Update",
  "sections": [{
    "activityTitle": "🎭 Theater Status Changed",
    "facts": [{
      "name": "Monitor:",
      "value": "{monitor_name}"
    }, {
      "name": "Location:",
      "value": "{location}"
    }, {
      "name": "Status:",
      "value": "{is_active}"
    }, {
      "name": "Timestamp:",
      "value": "{timestamp}"
    }],
    "markdown": true
  }]
}
```

---

## Discord

Send notifications to a Discord channel.

### Step 1: Create Discord Webhook
1. In Discord, go to Server Settings → Integrations → Webhooks
2. Create a new webhook
3. Copy the webhook URL

### Step 2: Configure Monitor Webhook

**Configuration**:
- Method: `POST`
- URL: `https://discord.com/api/webhooks/YOUR/WEBHOOK/URL`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "content": "🎭 **Theater Status Update**",
  "embeds": [{
    "title": "{monitor_name}",
    "fields": [
      {
        "name": "Location",
        "value": "{location}",
        "inline": true
      },
      {
        "name": "Status",
        "value": "{is_active}",
        "inline": true
      },
      {
        "name": "Timestamp",
        "value": "{timestamp}"
      }
    ],
    "color": 5814783
  }]
}
```

---

## Home Assistant

Trigger automations in Home Assistant.

### Method 1: Using Webhook Trigger

**Home Assistant Automation**:
```yaml
automation:
  - alias: "Theater Status Update"
    trigger:
      - platform: webhook
        webhook_id: "artsvision_theater_status"
    action:
      - service: input_boolean.turn_{{ trigger.json.is_active }}
        target:
          entity_id: input_boolean.{{ trigger.json.location | lower | replace(' ', '_') }}
```

**Monitor Webhook Configuration**:
- Method: `POST`
- URL: `http://homeassistant.local:8123/api/webhook/artsvision_theater_status`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "monitor_name": "{monitor_name}",
  "location": "{location}",
  "is_active": "{is_active}",
  "timestamp": "{timestamp}"
}
```

### Method 2: Using REST API

**Monitor Webhook Configuration**:
- Method: `POST`
- URL: `http://homeassistant.local:8123/api/states/sensor.theater_{location}`
- Headers:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_LONG_LIVED_ACCESS_TOKEN"
}
```
- Body Template:
```json
{
  "state": "{is_active}",
  "attributes": {
    "friendly_name": "Theater {location}",
    "monitor_name": "{monitor_name}",
    "last_updated": "{timestamp}"
  }
}
```

---

## Custom HTTP API

### Example 1: REST API with Authentication

**Configuration**:
- Method: `POST`
- URL: `https://api.your-system.com/v1/locations/status`
- Headers:
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key-here",
  "User-Agent": "ArtsVision-Monitor/1.0"
}
```
- Body Template:
```json
{
  "location_id": "{location}",
  "active": {is_active},
  "metadata": {
    "monitor": "{monitor_name}",
    "updated_at": "{timestamp}"
  }
}
```

### Example 2: MQTT Bridge

If you need to publish to MQTT, set up a simple bridge service:

**Simple Python MQTT Bridge** (runs separately):
```python
from flask import Flask, request
import paho.mqtt.client as mqtt

app = Flask(__name__)
mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt-broker-ip", 1883)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    topic = f"theater/{data['location']}/status"
    mqtt_client.publish(topic, str(data['is_active']))
    return "OK", 200

if __name__ == '__main__':
    app.run(port=5001)
```

**Monitor Webhook Configuration**:
- Method: `POST`
- URL: `http://localhost:5001/webhook`
- Headers:
```json
{
  "Content-Type": "application/json"
}
```
- Body Template:
```json
{
  "location": "{location}",
  "is_active": {is_active}
}
```

---

## Testing Webhooks

Always test your webhook configuration using the **"Test Webhook"** button in the monitor card.

You can also use tools like:
- **RequestBin** (https://requestbin.com) - Create temporary URLs to inspect webhook payloads
- **Webhook.site** (https://webhook.site) - Similar inspection tool
- **ngrok** (https://ngrok.com) - Expose local servers for testing

## Troubleshooting

**Webhook not triggering**:
- Verify the URL is accessible from the server
- Check that headers are valid JSON
- Ensure the remote system is listening on the correct port
- Review server logs for error messages

**Wrong data format**:
- Use the Test Webhook feature to see exactly what's being sent
- Verify template variable names are correct
- Check that the receiving system expects the format you're sending

**Authentication failures**:
- Double-check API keys, tokens, or credentials
- Ensure headers are formatted correctly
- Some systems require specific User-Agent strings

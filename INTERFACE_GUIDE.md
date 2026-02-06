# Dashboard Interface Guide

This document describes the visual layout and features of the ArtsVision Monitor Dashboard.

## Main Dashboard Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🎭 ArtsVision Monitor Dashboard                                          │
│                                                                            │
│  [+ Add Monitor]  [🔄 Refresh Now]  Last update: 2:30:45 PM              │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Monitor Card 1      │ Monitor Card 2      │ Monitor Card 3      │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

## Monitor Card (Active State)

```
┌─────────────────────────────────────────────┐
│  Walt Disney Theater Monitor        [✏️][🗑️]│
│  📍 Walt Disney Theater                     │
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐  │
│  │ 🟢 ACTIVE                            │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  CURRENT EVENT                              │
│  ┌──────────────────────────────────────┐  │
│  │ The Nutcracker                       │  │
│  │ 7:30 PM - 10:00 PM                   │  │
│  │ Inactive @ 11:00 PM (in 3h 15m)      │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  NEXT EVENT                                 │
│  ┌──────────────────────────────────────┐  │
│  │ Symphony Orchestra                   │  │
│  │ 2:00 PM - 4:30 PM                    │  │
│  │ Active @ 1:30 PM (in 19h 45m)        │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  🔗 Webhook Enabled                         │
│  [Test Webhook]                             │
└─────────────────────────────────────────────┘
```

## Monitor Card (Inactive State)

```
┌─────────────────────────────────────────────┐
│  Pugh Theater Monitor            [✏️][🗑️]   │
│  📍 Alexis & Jim Pugh Theater               │
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐  │
│  │ ⚪ Inactive                          │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  CURRENT EVENT                              │
│  No current event                           │
│                                             │
│  NEXT EVENT                                 │
│  ┌──────────────────────────────────────┐  │
│  │ Jazz Concert                         │  │
│  │ 8:00 PM - 10:30 PM                   │  │
│  │ Active @ 7:30 PM (in 5h)             │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Add/Edit Monitor Modal

```
┌───────────────────────────────────────────────────┐
│  Add Monitor                                  [×] │
├───────────────────────────────────────────────────┤
│                                                   │
│  Monitor Name *                                   │
│  [Main Theater Monitor________________]          │
│                                                   │
│  Location *                                       │
│  [Walt Disney Theater          ▼]                │
│                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Webhook Configuration                            │
│                                                   │
│  [✓] Enable Webhook                               │
│                                                   │
│  Webhook URL                                      │
│  [https://your-system.com/webhook___]            │
│                                                   │
│  HTTP Method                                      │
│  [POST                         ▼]                │
│                                                   │
│  Headers (JSON)                                   │
│  ┌───────────────────────────────────────┐       │
│  │ {                                     │       │
│  │   "Content-Type": "application/json"  │       │
│  │ }                                     │       │
│  └───────────────────────────────────────┘       │
│  Optional: Custom headers as JSON object         │
│                                                   │
│  Body Template (for POST)                         │
│  ┌───────────────────────────────────────┐       │
│  │ {                                     │       │
│  │   "location": "{location}",           │       │
│  │   "active": {is_active}               │       │
│  │ }                                     │       │
│  └───────────────────────────────────────┘       │
│  Available variables: monitor_id, monitor_name,  │
│  location, is_active, current_event, etc.        │
│                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                   │
│                      [Cancel]  [Save Monitor]    │
└───────────────────────────────────────────────────┘
```

## Empty State (No Monitors)

```
┌────────────────────────────────────────────────────┐
│                                                    │
│                                                    │
│              No monitors configured                │
│                                                    │
│        Click "Add Monitor" to create your          │
│                 first monitor                      │
│                                                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

## Visual States

### Status Indicators

**Active (Green, Pulsing)**
```
🟢 ACTIVE
```
The green dot pulses to indicate live active status.

**Inactive (Gray)**
```
⚪ Inactive
```
Static gray indicator for inactive monitors.

### Event Information Cards

Event cards have a colored left border (blue) and show:
- Event name (bold)
- Time range (HH:MM AM/PM format)
- Countdown to activation/deactivation

### Buttons and Actions

**Primary Actions** (Blue background)
- `[+ Add Monitor]`
- `[Save Monitor]`

**Secondary Actions** (Gray background)
- `[🔄 Refresh Now]`
- `[Test Webhook]`
- `[Cancel]`

**Edit/Delete** (Icon buttons)
- `[✏️]` - Edit monitor
- `[🗑️]` - Delete monitor

## Responsive Design

On mobile devices (< 768px width), the layout adapts:

```
┌─────────────────────┐
│ 🎭 ArtsVision      │
│    Monitor          │
│    Dashboard        │
├─────────────────────┤
│ [+ Add Monitor]     │
│ [🔄 Refresh Now]    │
│ Last update: 2:30   │
└─────────────────────┘

┌─────────────────────┐
│ Monitor Card 1      │
│ (full width)        │
└─────────────────────┘

┌─────────────────────┐
│ Monitor Card 2      │
│ (full width)        │
└─────────────────────┘

┌─────────────────────┐
│ Monitor Card 3      │
│ (full width)        │
└─────────────────────┘
```

## Color Scheme

The dashboard uses a clean, professional color palette:

- **Background**: Light gray (#f8fafc)
- **Cards**: White (#ffffff)
- **Primary (Buttons, Accents)**: Blue (#2563eb)
- **Success (Active status)**: Green (#10b981)
- **Text Primary**: Dark slate (#1e293b)
- **Text Secondary**: Gray (#64748b)
- **Borders**: Light gray (#e2e8f0)

## Real-Time Updates

When the server sends updates via WebSocket:
1. Monitor cards update automatically (no page refresh)
2. Status indicators change color/state
3. Event information updates
4. Countdowns refresh
5. Last update timestamp updates

## Keyboard & Accessibility

- Tab through interactive elements
- Enter/Space to activate buttons
- Escape to close modal
- Focus indicators on all interactive elements
- Semantic HTML for screen readers

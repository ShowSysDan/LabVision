#!/bin/bash
# ============================================================================
# LabVision - Debian/Ubuntu Install Script
#
# Sets up the application as a systemd service that:
#   - Creates a virtual environment and installs dependencies
#   - Installs and enables a systemd service
#   - Starts automatically on boot
#   - Restarts automatically if it crashes
#
# Usage:
#   sudo bash install.sh
#
# After install:
#   - Dashboard: http://<your-ip>:5000
#   - Configure API key via Settings button in the dashboard
#
# Service commands:
#   sudo systemctl status labvision
#   sudo systemctl restart labvision
#   sudo systemctl stop labvision
#   sudo journalctl -u labvision -f
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo "  LabVision - Service Installer"
echo "============================================"
echo ""

# Must run as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (sudo bash install.sh)${NC}"
    exit 1
fi

# Detect the actual user (not root) who called sudo
ACTUAL_USER="${SUDO_USER:-$(whoami)}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${YELLOW}Warning: Running as root user. The service will run as root.${NC}"
    echo -e "${YELLOW}For production, consider running under a dedicated user.${NC}"
fi

# Get the directory where this script lives
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="labvision"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo -e "Install directory: ${GREEN}$INSTALL_DIR${NC}"
echo -e "Service user:      ${GREEN}$ACTUAL_USER${NC}"
echo ""

# ---- Step 1: Install system dependencies ----
echo -e "${YELLOW}[1/5] Checking system dependencies...${NC}"
apt-get update -qq

# Install python3 and venv if not present
for pkg in python3 python3-venv python3-pip; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        echo "  Installing $pkg..."
        apt-get install -y -qq "$pkg"
    else
        echo "  $pkg already installed"
    fi
done

# ---- Step 2: Create virtual environment ----
echo ""
echo -e "${YELLOW}[2/5] Setting up Python virtual environment...${NC}"

if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "  Virtual environment already exists"
fi

# ---- Step 3: Install Python dependencies ----
echo ""
echo -e "${YELLOW}[3/5] Installing Python dependencies...${NC}"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# Fix ownership if we created venv as root
chown -R "$ACTUAL_USER":"$ACTUAL_USER" "$VENV_DIR" 2>/dev/null || true
chown -R "$ACTUAL_USER":"$ACTUAL_USER" "$INSTALL_DIR/instance" 2>/dev/null || true

# ---- Step 4: Create systemd service ----
echo ""
echo -e "${YELLOW}[4/5] Installing systemd service...${NC}"

cat > "$SERVICE_FILE" << SERVICEEOF
[Unit]
Description=LabVision Monitor Dashboard
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python app.py
Environment="PYTHONUNBUFFERED=1"

# Restart policy - always restart, wait 10s between attempts
Restart=always
RestartSec=10

# Stop gracefully (SIGTERM), then force after 30s
TimeoutStopSec=30
KillSignal=SIGTERM

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "  Service file written to $SERVICE_FILE"

# ---- Step 5: Enable and start ----
echo ""
echo -e "${YELLOW}[5/5] Enabling and starting service...${NC}"

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Stop if already running, then start fresh
systemctl restart "$SERVICE_NAME"

# Wait a moment for startup
sleep 2

# Check status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Installation complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "  Dashboard:  http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "  Next step:  Open the dashboard and click Settings"
    echo "              to enter your API key."
    echo ""
    echo "  Useful commands:"
    echo "    sudo systemctl status $SERVICE_NAME"
    echo "    sudo systemctl restart $SERVICE_NAME"
    echo "    sudo systemctl stop $SERVICE_NAME"
    echo "    sudo journalctl -u $SERVICE_NAME -f"
    echo ""
else
    echo ""
    echo -e "${RED}Service failed to start. Check logs:${NC}"
    echo "  sudo journalctl -u $SERVICE_NAME --no-pager -n 30"
    exit 1
fi

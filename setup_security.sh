#!/bin/bash

# XOCOA Server Hardening Script
# Usage: sudo ./setup_security.sh

echo "🛡️  [XOCOA] Starting Security Hardening..."

# 1. Update System
apt-get update && apt-get upgrade -y

# 2. Install Essentials
apt-get install -y ufw fail2ban curl git htop

# 3. Configure Firewall (UFW)
echo "🔥 [XOCOA] Configuring Firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 4. Configure Fail2Ban
echo "🚫 [XOCOA] Configuring Fail2Ban..."
systemctl enable fail2ban
systemctl start fail2ban

# 5. Install Docker (if missing)
if ! command -v docker &> /dev/null
then
    echo "🐳 [XOCOA] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

echo "✅ [XOCOA] Server is secured and ready."

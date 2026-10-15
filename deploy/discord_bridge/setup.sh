#!/usr/bin/env bash
# One-time install of the Discord alert bridge on a fresh Ubuntu 24.04 server.
# Run as root:   bash setup.sh
# Re-running is safe: it updates the code and keeps your existing settings.
set -euo pipefail

REPO="https://github.com/lukejackson9-cloud/TRADING-BOT-..git"
BRANCH="${BRANCH:-ccr-471a116f-0q22sz}"
APP=/opt/trading-bot
DATA=/var/lib/discord-bridge
ENVF=/etc/discord-bridge.env

[ "$(id -u)" = 0 ] || { echo "Run as root (sudo bash setup.sh)"; exit 1; }

echo "== Installing packages"
apt-get update -qq
apt-get install -y -qq git python3 python3-requests caddy ufw openssl curl >/dev/null

echo "== Fetching code (branch $BRANCH)"
id bridge >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin bridge
if [ -d "$APP/.git" ]; then
  git -C "$APP" fetch -q origin "$BRANCH" && git -C "$APP" checkout -q -B "$BRANCH" "origin/$BRANCH"
else
  git clone -q --branch "$BRANCH" "$REPO" "$APP"
fi
mkdir -p "$DATA" && chown -R bridge:bridge "$DATA"

if [ ! -f "$ENVF" ]; then
  echo "== First-time settings"
  read -rp  "Trading 212 DEMO API key: " T212_KEY
  read -rsp "Trading 212 DEMO API secret: " T212_SECRET; echo
  SECRET=$(openssl rand -hex 24)
  TOPIC="bridge-$(openssl rand -hex 8)"
  umask 077
  cat > "$ENVF" <<EOF
T212_API_KEY=$T212_KEY
T212_API_SECRET=$T212_SECRET
T212_BASE_URL=https://demo.trading212.com/api/v0
BRIDGE_SECRET=$SECRET
NTFY_TOPIC=$TOPIC
BRIDGE_HOST=127.0.0.1
BRIDGE_PORT=8787
BRIDGE_STATE_DIR=$DATA
BRIDGE_TRADES_LOG=$DATA/trades.log
# Test mode: alerts are read and logged, NO orders. Set to 0 once the log
# shows real alerts being read correctly, then: systemctl restart discord-bridge
BRIDGE_DRY_RUN=1
# Only act on notifications containing this text (set after seeing a real one)
BRIDGE_CHANNEL_FILTER=
EOF
  chown root:bridge "$ENVF"; chmod 640 "$ENVF"
fi

echo "== Service"
cat > /etc/systemd/system/discord-bridge.service <<EOF
[Unit]
Description=Discord alert bridge -> Trading 212 demo
After=network-online.target
Wants=network-online.target

[Service]
User=bridge
EnvironmentFile=$ENVF
WorkingDirectory=$APP
ExecStart=/usr/bin/python3 $APP/scripts/discord_alert_bridge.py serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
cat > /usr/local/bin/bridge <<EOF
#!/usr/bin/env bash
# bridge status | bridge resume | bridge parse "some alert text" | bridge update | bridge log
case "\${1:-status}" in
  update) BRANCH=$BRANCH bash $APP/deploy/discord_bridge/setup.sh ;;
  log)    journalctl -u discord-bridge -f ;;
  *)      sudo -u bridge bash -c 'set -a; . $ENVF; set +a; exec python3 $APP/scripts/discord_alert_bridge.py "\$@"' _ "\$@" ;;
esac
EOF
chmod 755 /usr/local/bin/bridge
systemctl daemon-reload
systemctl enable -q discord-bridge
systemctl restart discord-bridge

echo "== HTTPS (Caddy, free certificate via sslip.io)"
IP=$(curl -s -4 https://api.ipify.org)
HOST="${IP//./-}.sslip.io"
cat > /etc/caddy/Caddyfile <<EOF
$HOST {
    reverse_proxy 127.0.0.1:8787
}
EOF
systemctl restart caddy
ufw allow OpenSSH >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

set -a; . "$ENVF"; set +a
cat <<EOF

=====================================================================
 Installed. Give the certificate ~1 minute, then check:
   curl https://$HOST/health        (should print: ok)

 For the phone app (keep these private):
   URL:     https://$HOST/alert
   Header:  X-Bridge-Secret: $BRIDGE_SECRET

 Trade notifications: install the "ntfy" app, subscribe to topic:
   $NTFY_TOPIC

 Watch it live:    journalctl -u discord-bridge -f
 Mode: TEST (no orders) until BRIDGE_DRY_RUN=0 in $ENVF
=====================================================================
EOF

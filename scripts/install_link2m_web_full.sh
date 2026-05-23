#!/usr/bin/env bash
set -e

APP_DIR=/opt/king3399-web
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$APP_DIR/static"

if [ -f "$APP_DIR/app.py" ]; then
  cp "$APP_DIR/app.py" "$APP_DIR/app.py.bak.$(date +%F-%H%M%S)"
fi

cp "$REPO_DIR/web/app.py" "$APP_DIR/app.py"
cp -a "$REPO_DIR/web/static/." "$APP_DIR/static/" 2>/dev/null || true

python3 -m py_compile "$APP_DIR/app.py"

cat > /etc/systemd/system/king3399-web.service <<'EOF'
[Unit]
Description=Link2M Hardware Web Center
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/king3399-web
ExecStart=/usr/bin/python3 /opt/king3399-web/app.py
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now king3399-web.service
systemctl restart king3399-web.service
systemctl status king3399-web.service --no-pager

IP="$(hostname -I | awk '{print $1}')"
echo
echo "OK: Link2M Hardware Center installed."
echo "Open: http://${IP}:8080"

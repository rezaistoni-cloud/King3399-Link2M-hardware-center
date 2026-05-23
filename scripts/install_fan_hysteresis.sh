#!/usr/bin/env bash
set -e

ON_TEMP="${ON_TEMP:-45000}"
OFF_TEMP="${OFF_TEMP:-38000}"

cat > /usr/local/sbin/link2m-fan-hysteresis.sh <<EOF
#!/usr/bin/env bash
ON_TEMP=$ON_TEMP
OFF_TEMP=$OFF_TEMP
STATE=0

while true; do
  FANDEV=\$(for c in /sys/class/thermal/cooling_device*; do
    [ "\$(cat "\$c/type" 2>/dev/null)" = "gpio-fan" ] && echo "\$c"
  done | head -n1)

  MAXTEMP=\$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -nr | head -n1)

  if [ -n "\$FANDEV" ] && [ -n "\$MAXTEMP" ]; then
    if [ "\$MAXTEMP" -ge "\$ON_TEMP" ]; then
      STATE=1
    elif [ "\$MAXTEMP" -le "\$OFF_TEMP" ]; then
      STATE=0
    fi
    echo "\$STATE" > "\$FANDEV/cur_state" 2>/dev/null || true
  fi

  sleep 3
done
EOF

chmod +x /usr/local/sbin/link2m-fan-hysteresis.sh

cat > /etc/systemd/system/link2m-fan-hysteresis.service <<'EOF'
[Unit]
Description=Link2M GPIO Fan Hysteresis Control
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/sbin/link2m-fan-hysteresis.sh
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl disable king3399-fan-loop.service king3399-fan-hysteresis.service 2>/dev/null || true
systemctl enable --now link2m-fan-hysteresis.service
systemctl restart link2m-fan-hysteresis.service
systemctl status link2m-fan-hysteresis.service --no-pager

echo "OK: fan hysteresis installed. ON=${ON_TEMP} OFF=${OFF_TEMP}"

# 05 - Link2M Web Dashboard

Dashboard web berada di:

```text
web/app.py
```

Install:

```bash
bash scripts/install_link2m_web_full.sh
```

Cek service:

```bash
systemctl status king3399-web.service --no-pager
journalctl -u king3399-web.service -n 80 --no-pager
```

Buka:

```text
http://192.168.1.15:8080
```

## Endpoint API utama

```text
GET  /api/status
GET  /api/wifi/scan
GET  /api/wifi/profiles
POST /api/wifi/connect
POST /api/wifi/reconnect
POST /api/wifi/forget
POST /api/wifi/autoreconnect
POST /api/wifi/keepalive
POST /api/eth/dhcp
POST /api/eth/static
POST /api/fan/save
POST /api/fan/restart
POST /api/modem/restart
POST /api/modem/scan
POST /api/test/default
POST /api/test/wwan
POST /api/power/reboot
POST /api/power/off
```

## UI Features

- Header Link2M + Arwito Tech.
- Card status:
  - Temperature
  - LAN Ethernet
  - WLAN WiFi
  - WWAN LTE
  - Uptime
- Device Summary:
  - Wi-Fi
  - Bluetooth
  - Modem USB
  - USB Storage
  - HDMI
  - SD Card
- Fan hysteresis setting.
- Wi-Fi scan, connect, reconnect, forget, auto reconnect, keepalive.
- Ethernet DHCP/static.
- Modem restart/scan.
- Internet test.
- Reboot and power off.

## Jika web blank

Jangan edit CSS dulu. Cek error Python:

```bash
python3 -m py_compile /opt/king3399-web/app.py
journalctl -u king3399-web.service -n 100 --no-pager
```

Restore backup:

```bash
ls -lh /opt/king3399-web/app.py.bak*
cp /opt/king3399-web/app.py.bak.NAMA_BACKUP /opt/king3399-web/app.py
systemctl restart king3399-web.service
```

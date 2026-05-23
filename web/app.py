#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from pathlib import Path
import subprocess, os, re, time, glob, shlex

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="/static")

def run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "out": (p.stdout or "").strip(),
            "err": (p.stderr or "").strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": 124, "out": "", "err": "timeout", "cmd": cmd}
    except Exception as e:
        return {"ok": False, "code": 1, "out": "", "err": str(e), "cmd": cmd}

def read_text(path, default=""):
    try:
        return Path(path).read_text(errors="ignore").strip()
    except Exception:
        return default

def write_text(path, data):
    Path(path).write_text(data)

def safe_iface(name):
    return name if re.match(r"^[a-zA-Z0-9_.:-]+$", name or "") else ""

def get_ip(iface):
    iface = safe_iface(iface)
    if not iface:
        return "-"
    p = run(f"ip -4 -o addr show dev {shlex.quote(iface)} | awk '{{print $4}}' | cut -d/ -f1 | head -n1")
    return p["out"] if p["out"] else "-"

def get_link_state(iface):
    iface = safe_iface(iface)
    if not iface:
        return "unknown"
    oper = read_text(f"/sys/class/net/{iface}/operstate", "")
    if oper:
        return oper
    p = run(f"ip link show dev {shlex.quote(iface)}")
    return "present" if p["ok"] else "not present"

def uptime_text():
    raw = read_text("/proc/uptime", "0")
    try:
        sec = int(float(raw.split()[0]))
    except Exception:
        sec = 0
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m} minutes"

def max_temp_c():
    vals = []
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            v = int(read_text(f, "0"))
            if v > 1000:
                vals.append(v / 1000.0)
            elif v > 0:
                vals.append(float(v))
        except Exception:
            pass
    return round(max(vals), 1) if vals else None

def fan_device():
    for c in glob.glob("/sys/class/thermal/cooling_device*"):
        if read_text(f"{c}/type", "") == "gpio-fan":
            return c
    return ""

def fan_info():
    dev = fan_device()
    on_temp = 45
    off_temp = 38
    script = Path("/usr/local/sbin/link2m-fan-hysteresis.sh")
    if not script.exists():
        script = Path("/usr/local/sbin/king3399-fan-hysteresis.sh")
    if script.exists():
        s = read_text(script)
        m = re.search(r"ON_TEMP=(\d+)", s)
        if m:
            on_temp = int(m.group(1)) // 1000
        m = re.search(r"OFF_TEMP=(\d+)", s)
        if m:
            off_temp = int(m.group(1)) // 1000
    return {
        "device": dev or "-",
        "type": read_text(f"{dev}/type", "-") if dev else "-",
        "cur_state": read_text(f"{dev}/cur_state", "0") if dev else "0",
        "max_state": read_text(f"{dev}/max_state", "1") if dev else "1",
        "service": "active" if run("systemctl is-active --quiet link2m-fan-hysteresis.service || systemctl is-active --quiet king3399-fan-hysteresis.service")["ok"] else "inactive",
        "on_c": on_temp,
        "off_c": off_temp,
    }

def install_fan_hysteresis(on_c, off_c):
    on_c = int(on_c)
    off_c = int(off_c)
    if on_c <= off_c:
        return {"ok": False, "err": "ON temperature must be higher than OFF temperature."}
    if on_c < 35 or on_c > 80 or off_c < 25 or off_c > 75:
        return {"ok": False, "err": "Temperature range not safe. Use ON 35-80 and OFF 25-75."}

    script = f'''#!/usr/bin/env bash
ON_TEMP={on_c * 1000}
OFF_TEMP={off_c * 1000}
STATE=0

while true; do
  FANDEV=$(for c in /sys/class/thermal/cooling_device*; do
    [ "$(cat "$c/type" 2>/dev/null)" = "gpio-fan" ] && echo "$c"
  done | head -n1)

  MAXTEMP=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -nr | head -n1)

  if [ -n "$FANDEV" ] && [ -n "$MAXTEMP" ]; then
    if [ "$MAXTEMP" -ge "$ON_TEMP" ]; then
      STATE=1
    elif [ "$MAXTEMP" -le "$OFF_TEMP" ]; then
      STATE=0
    fi
    echo "$STATE" > "$FANDEV/cur_state" 2>/dev/null
  fi

  sleep 3
done
'''
    service = '''[Unit]
Description=Link2M GPIO Fan Hysteresis Control
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/sbin/link2m-fan-hysteresis.sh
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
'''
    write_text("/usr/local/sbin/link2m-fan-hysteresis.sh", script)
    os.chmod("/usr/local/sbin/link2m-fan-hysteresis.sh", 0o755)
    write_text("/etc/systemd/system/link2m-fan-hysteresis.service", service)
    run("systemctl daemon-reload")
    run("systemctl disable king3399-fan-loop.service king3399-fan-hysteresis.service 2>/dev/null || true")
    run("systemctl enable --now link2m-fan-hysteresis.service")
    run("systemctl restart link2m-fan-hysteresis.service")
    return {"ok": True, "out": "fan hysteresis saved and service restarted"}

def storage_info():
    return run("lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL 2>/dev/null")["out"]

def sd_present():
    return os.path.exists("/dev/mmcblk1") or os.path.exists("/dev/mmcblk1p1")

def usb_storage_present():
    p = run("lsblk -dn -o NAME,TRAN,TYPE 2>/dev/null | awk '$2==\"usb\" && $3==\"disk\" {print $1}'")
    return bool(p["out"])

def hdmi_info():
    conns = []
    for st in glob.glob("/sys/class/drm/card*-HDMI-A-*/status"):
        base = Path(st).parent
        status = read_text(st, "unknown")
        modes = read_text(base / "modes", "").splitlines()
        conns.append({"name": base.name, "status": status, "modes": modes[:8]})
    return {
        "connected": any(x["status"] == "connected" for x in conns),
        "connectors": conns,
        "fb": os.path.exists("/dev/fb0"),
    }

def modem_info():
    nodes = sorted(glob.glob("/dev/cdc-wdm*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    mm = run("mmcli -L 2>/dev/null")
    modem_path = ""
    if mm["out"]:
        m = re.search(r"Modem/([0-9]+)", mm["out"])
        if m:
            modem_path = m.group(1)
    detail = run(f"mmcli -m {modem_path} 2>/dev/null", timeout=10)["out"] if modem_path else ""
    sim_state = "unknown"
    if "sim-missing" in detail:
        sim_state = "sim-missing"
    elif "sim slot paths:" in detail:
        sim_state = "detected"
    return {
        "usb_present": bool(nodes),
        "nodes": nodes,
        "mmcli_list": mm["out"] or "No modem listed by ModemManager",
        "modem_id": modem_path or "-",
        "sim": sim_state,
        "detail": detail,
    }

def wifi_profiles():
    p = run("nmcli -t -f NAME,TYPE,AUTOCONNECT con show 2>/dev/null")
    items = []
    for line in p["out"].splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[1] == "802-11-wireless":
            items.append({"name": parts[0], "autoconnect": parts[2] if len(parts) > 2 else ""})
    return items

def dashboard_status():
    return {
        "product": "Link2M",
        "subtitle": "ARWITO TECH",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": uptime_text(),
        "temperature_c": max_temp_c(),
        "network": {
            "eth0": {"ip": get_ip("eth0"), "state": get_link_state("eth0")},
            "wlan0": {"ip": get_ip("wlan0"), "state": get_link_state("wlan0")},
            "wwan0": {"ip": get_ip("wwan0"), "state": get_link_state("wwan0")},
        },
        "fan": fan_info(),
        "devices": {
            "hdmi": hdmi_info(),
            "sd_card": {"present": sd_present(), "storage": storage_info()},
            "usb_storage": {"present": usb_storage_present()},
            "wifi": {"present": os.path.exists("/sys/class/net/wlan0")},
            "bluetooth": {"present": "hci0" in run("rfkill list 2>/dev/null")["out"]},
            "modem": modem_info(),
        },
        "system": {
            "loadavg": read_text("/proc/loadavg", "-"),
            "memory": run("free -h 2>/dev/null")["out"],
            "disk": run("df -h / 2>/dev/null")["out"],
        }
    }

@app.get("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")

@app.get("/api/status")
def api_status():
    return jsonify(dashboard_status())

@app.get("/api/net/ips")
def api_net_ips():
    return jsonify(dashboard_status()["network"])

@app.post("/api/fan/save")
def api_fan_save():
    data = request.get_json(force=True, silent=True) or {}
    res = install_fan_hysteresis(data.get("on_c", 45), data.get("off_c", 38))
    return jsonify(res), (200 if res.get("ok") else 400)

@app.post("/api/fan/restart")
def api_fan_restart():
    return jsonify(run("systemctl restart link2m-fan-hysteresis.service || systemctl restart king3399-fan-hysteresis.service"))

@app.get("/api/wifi/scan")
def api_wifi_scan():
    run("rfkill unblock wifi 2>/dev/null || true")
    p = run("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list ifname wlan0 --rescan yes 2>/dev/null", timeout=15)
    items = []
    for line in p["out"].splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            items.append({
                "active": parts[0] == "*",
                "ssid": parts[1].replace("\\:", ":"),
                "signal": parts[2],
                "security": ":".join(parts[3:]).replace("\\:", ":"),
            })
    return jsonify({"ok": p["ok"], "items": items, "raw": p["out"], "err": p["err"]})

@app.get("/api/wifi/profiles")
def api_wifi_profiles():
    return jsonify({"ok": True, "items": wifi_profiles()})

@app.post("/api/wifi/connect")
def api_wifi_connect():
    data = request.get_json(force=True, silent=True) or {}
    ssid = str(data.get("ssid", "")).strip()
    password = str(data.get("password", ""))
    if not ssid:
        return jsonify({"ok": False, "err": "SSID is required"}), 400
    cmd = f"nmcli dev wifi connect {shlex.quote(ssid)}"
    if password:
        cmd += f" password {shlex.quote(password)}"
    cmd += " ifname wlan0"
    return jsonify(run(cmd, timeout=30))

@app.post("/api/wifi/reconnect")
def api_wifi_reconnect():
    return jsonify(run("nmcli dev disconnect wlan0 2>/dev/null; sleep 2; nmcli dev connect wlan0 2>/dev/null", timeout=20))

@app.post("/api/wifi/forget")
def api_wifi_forget():
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"ok": False, "err": "Profile name is required"}), 400
    return jsonify(run(f"nmcli con delete {shlex.quote(name)}", timeout=15))

@app.post("/api/wifi/autoreconnect")
def api_wifi_autoreconnect():
    data = request.get_json(force=True, silent=True) or {}
    enable = bool(data.get("enable", True))
    val = "yes" if enable else "no"
    name = str(data.get("name", "")).strip()
    if name:
        cmd = f"nmcli con mod {shlex.quote(name)} connection.autoconnect {val}"
    else:
        cmd = "for c in $(nmcli -t -f NAME,TYPE con show | awk -F: '$2==\"802-11-wireless\"{print $1}'); do nmcli con mod \"$c\" connection.autoconnect " + val + "; done"
    return jsonify(run(cmd, timeout=20))

@app.post("/api/wifi/keepalive")
def api_wifi_keepalive():
    data = request.get_json(force=True, silent=True) or {}
    enable = bool(data.get("enable", True))
    service = '''[Unit]
Description=Link2M WiFi Keepalive
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/sbin/link2m-wifi-keepalive.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
    script = '''#!/usr/bin/env bash
while true; do
  if ip link show wlan0 >/dev/null 2>&1; then
    if ! ping -I wlan0 -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
      nmcli dev connect wlan0 >/dev/null 2>&1 || true
    fi
  fi
  sleep 30
done
'''
    write_text("/usr/local/sbin/link2m-wifi-keepalive.sh", script)
    os.chmod("/usr/local/sbin/link2m-wifi-keepalive.sh", 0o755)
    write_text("/etc/systemd/system/link2m-wifi-keepalive.service", service)
    run("systemctl daemon-reload")
    if enable:
        res = run("systemctl enable --now link2m-wifi-keepalive.service")
    else:
        res = run("systemctl disable --now link2m-wifi-keepalive.service")
    return jsonify(res)

@app.post("/api/eth/dhcp")
def api_eth_dhcp():
    conn = run("nmcli -g GENERAL.CONNECTION dev show eth0 2>/dev/null | head -n1")["out"] or "Wired connection 1"
    cmd = f"nmcli con mod {shlex.quote(conn)} ipv4.method auto ipv4.addresses '' ipv4.gateway '' ipv4.dns ''; nmcli con up {shlex.quote(conn)}"
    return jsonify(run(cmd, timeout=20))

@app.post("/api/eth/static")
def api_eth_static():
    data = request.get_json(force=True, silent=True) or {}
    ip = str(data.get("ip", "")).strip()
    gw = str(data.get("gateway", "")).strip()
    dns = str(data.get("dns", "8.8.8.8")).strip()
    if not ip or not gw:
        return jsonify({"ok": False, "err": "IP/CIDR and gateway are required"}), 400
    conn = run("nmcli -g GENERAL.CONNECTION dev show eth0 2>/dev/null | head -n1")["out"] or "Wired connection 1"
    cmd = f"nmcli con mod {shlex.quote(conn)} ipv4.method manual ipv4.addresses {shlex.quote(ip)} ipv4.gateway {shlex.quote(gw)} ipv4.dns {shlex.quote(dns)}; nmcli con up {shlex.quote(conn)}"
    return jsonify(run(cmd, timeout=20))

@app.post("/api/modem/restart")
def api_modem_restart():
    return jsonify(run("systemctl restart ModemManager", timeout=20))

@app.post("/api/modem/scan")
def api_modem_scan():
    return jsonify(run("mmcli -S; sleep 5; mmcli -L", timeout=20))

@app.post("/api/test/default")
def api_test_default():
    return jsonify(run("ping -c 3 -W 3 8.8.8.8", timeout=15))

@app.post("/api/test/wwan")
def api_test_wwan():
    return jsonify(run("ping -I wwan0 -c 3 -W 3 8.8.8.8", timeout=15))

@app.post("/api/power/reboot")
def api_power_reboot():
    run("(sleep 1; systemctl reboot) >/dev/null 2>&1 &", timeout=2)
    return jsonify({"ok": True, "out": "Reboot requested"})

@app.post("/api/power/off")
def api_power_off():
    run("(sleep 1; systemctl poweroff) >/dev/null 2>&1 &", timeout=2)
    return jsonify({"ok": True, "out": "Power off requested"})

INDEX_HTML = r'''
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Link2M Hardware Center</title>
<style>
:root{--bg:#f5f7fb;--panel:#fff;--line:#e4e7ec;--text:#101828;--muted:#667085;--blue:#255be8;--blue2:#1d4ed8;--green:#067647;--green-bg:#ecfdf3;--red:#b42318;--red-bg:#fef3f2;--orange:#b54708;--orange-bg:#fff6ed;--shadow:0 16px 42px rgba(16,24,40,.08)}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Roboto,Arial,sans-serif}button,input,select{font:inherit}.app{min-height:100vh}
.topbar{position:sticky;top:0;z-index:20;height:118px;background:rgba(255,255,255,.94);backdrop-filter:blur(16px);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:14px 42px}
.brand{display:flex;align-items:center;gap:18px;min-width:300px}.logo-img{height:76px;max-width:340px;object-fit:contain}.brand-fallback{display:none;font-weight:900;font-size:38px;letter-spacing:-.04em;color:#0f172a}.brand-sub{font-size:13px;font-weight:900;letter-spacing:.24em;color:#667085;margin-top:2px}
.actions{display:flex;gap:12px;align-items:center}.icon-btn,.primary-btn,.warn-btn,.danger-btn,.ghost-btn{border:0;border-radius:16px;cursor:pointer;font-weight:800;transition:.15s ease}.icon-btn{width:54px;height:54px;background:#fff;border:1px solid var(--line);color:#475467}.primary-btn{background:var(--blue);color:#fff;padding:16px 28px;box-shadow:0 12px 24px rgba(37,91,232,.22)}.primary-btn:hover{background:var(--blue2)}.warn-btn{background:#ea8c00;color:#fff;padding:13px 18px}.danger-btn{background:#dc2626;color:#fff;padding:13px 18px}.ghost-btn{background:#fff;color:var(--blue);border:1px solid #bfd4ff;padding:13px 18px}
.main{padding:28px 42px 60px}.hero{background:linear-gradient(180deg,#fff,#fbfdff);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:30px;padding:34px;margin-bottom:26px}.hero h1{font-size:34px;line-height:1.1;margin:0 0 12px;font-weight:900;letter-spacing:-.03em}.hero p{margin:0 0 26px;color:var(--muted);font-size:18px;line-height:1.5}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px}.metric{min-height:132px;background:#fff;border:1px solid var(--line);border-radius:22px;padding:24px;display:flex;flex-direction:column;justify-content:center}.metric-label{font-size:15px;font-weight:800;color:var(--muted);margin-bottom:14px}.metric-value{font-size:28px;font-weight:900;letter-spacing:-.03em;color:var(--text)}.metric-sub{font-size:13px;font-weight:700;color:var(--muted);margin-top:10px}
.section{background:#fff;border:1px solid var(--line);box-shadow:0 12px 30px rgba(16,24,40,.05);border-radius:26px;padding:28px;margin-bottom:24px}.section-title{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px}.section-title h2{font-size:22px;margin:0;font-weight:900;letter-spacing:-.02em}.grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.card{border:1px solid var(--line);border-radius:22px;background:#fff;padding:22px;min-height:150px}.card h3{margin:0 0 16px;font-size:17px;font-weight:900;color:#344054}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid #f2f4f7}.row:last-child{border-bottom:0}.k{color:var(--muted);font-weight:700}.v{font-weight:900;text-align:right}.badge{display:inline-flex;align-items:center;border-radius:999px;padding:7px 11px;font-size:13px;font-weight:900}.ok{background:var(--green-bg);color:var(--green)}.bad{background:var(--red-bg);color:var(--red)}.warn{background:var(--orange-bg);color:var(--orange)}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.input-wrap{display:flex;flex-direction:column;gap:8px}.input-wrap label{font-size:13px;font-weight:900;color:var(--muted)}.input,select{width:100%;height:50px;border:1px solid var(--line);border-radius:15px;padding:0 14px;background:#fff;color:var(--text);outline:none}.password-wrap{position:relative}.password-wrap .input{padding-right:48px}.eye{position:absolute;right:10px;top:8px;border:0;background:#f2f4f7;border-radius:11px;width:34px;height:34px;cursor:pointer}
.btn-row{display:flex;flex-wrap:wrap;gap:12px;margin-top:16px}.btn-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}.btn-grid button{height:56px}
pre{margin:0;background:#0b1020;color:#e5e7eb;border-radius:18px;padding:18px;overflow:auto;max-height:320px;font-size:13px;line-height:1.45}.log{margin-top:16px;min-height:50px;background:#0b1020;color:#d1d5db;border-radius:16px;padding:14px;font-size:13px;white-space:pre-wrap}.table{width:100%;border-collapse:collapse;font-size:14px}.table th,.table td{border-bottom:1px solid #eef2f7;text-align:left;padding:12px}.table th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}.footer{color:var(--muted);font-size:13px;text-align:center;padding:20px}
@media(max-width:1200px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-3{grid-template-columns:1fr}.grid-2{grid-template-columns:1fr}}@media(max-width:720px){.topbar{height:auto;padding:14px 18px;align-items:flex-start;gap:12px}.main{padding:18px}.logo-img{height:54px;max-width:240px}.metrics{grid-template-columns:1fr}.form-grid{grid-template-columns:1fr}.btn-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="app">
<header class="topbar"><div class="brand"><div><img class="logo-img" src="/static/link2m.svg" alt="Link2M" onerror="this.style.display='none';document.querySelector('.brand-fallback').style.display='block'"><div class="brand-fallback">Link<span style="color:#0ea5e9">2M</span></div><div class="brand-sub">ARWITO TECH</div></div></div><div class="actions"><button class="icon-btn" onclick="scrollToSection('settings')">⚙</button><button class="icon-btn" onclick="scrollToSection('devices')">☷</button><button class="primary-btn" onclick="refreshAll()">Refresh</button></div></header>
<main class="main">
<section class="hero"><h1>Industrial Gateway Monitoring</h1><p>Professional hardware dashboard for thermal control, HDMI, SD card, USB devices, LTE modem, Bluetooth, Wi-Fi, Ethernet and system health.</p><div class="metrics"><div class="metric"><div class="metric-label">Temperature</div><div class="metric-value" id="mTemp">-</div><div class="metric-sub">thermal max</div></div><div class="metric"><div class="metric-label">LAN Ethernet</div><div class="metric-value" id="mEth">-</div><div class="metric-sub" id="sEth">eth0</div></div><div class="metric"><div class="metric-label">WLAN WiFi</div><div class="metric-value" id="mWlan">-</div><div class="metric-sub" id="sWlan">wlan0</div></div><div class="metric"><div class="metric-label">WWAN LTE</div><div class="metric-value" id="mWwan">-</div><div class="metric-sub" id="sWwan">wwan0</div></div><div class="metric"><div class="metric-label">Uptime</div><div class="metric-value" id="mUptime">-</div><div class="metric-sub" id="mTime">-</div></div></div></section>
<section class="section" id="devices"><div class="section-title"><h2>Device Summary</h2><span id="overall" class="badge warn">checking</span></div><div class="grid-3"><div class="card"><h3>Core Hardware</h3><div id="coreRows"></div></div><div class="card"><h3>Storage & Display</h3><div id="storageRows"></div></div><div class="card"><h3>LTE Modem</h3><div id="modemRows"></div></div></div></section>
<section class="section" id="settings"><div class="section-title"><h2>Fan Hysteresis Control</h2><span id="fanBadge" class="badge warn">checking</span></div><div class="grid-2"><div class="card"><h3>Thermal Saving Mode</h3><div class="form-grid"><div class="input-wrap"><label>Fan ON temperature °C</label><input id="fanOn" class="input" type="number" min="35" max="80" value="45"></div><div class="input-wrap"><label>Fan OFF temperature °C</label><input id="fanOff" class="input" type="number" min="25" max="75" value="38"></div></div><div class="btn-row"><button class="primary-btn" onclick="saveFan()">Save Hysteresis</button><button class="ghost-btn" onclick="post('/api/fan/restart')">Restart Fan</button></div><div class="log" id="fanLog">Ready.</div></div><div class="card"><h3>Current Fan State</h3><div id="fanRows"></div></div></div></section>
<section class="section"><div class="section-title"><h2>Wi-Fi Manager</h2><span id="wifiBadge" class="badge warn">checking</span></div><div class="grid-2"><div class="card"><h3>Scan & Connect</h3><div class="form-grid"><div class="input-wrap"><label>SSID</label><select id="ssid"></select></div><div class="input-wrap"><label>Password</label><div class="password-wrap"><input id="wifiPass" class="input" type="password" placeholder="Wi-Fi password"><button class="eye" onclick="togglePass()" type="button">👁</button></div></div></div><div class="btn-grid"><button class="ghost-btn" onclick="scanWifi()">Refresh Profiles</button><button class="primary-btn" onclick="connectWifi()">Connect Selected</button><button class="warn-btn" onclick="wifiAuto(true)">Auto Reconnect ON</button><button class="ghost-btn" onclick="wifiKeepalive(false)">Keepalive OFF</button><button class="primary-btn" onclick="reconnectWifi()">Reconnect Selected</button><button class="ghost-btn" onclick="forgetWifi()">Forget Selected</button></div><div class="log" id="wifiLog">Ready.</div></div><div class="card"><h3>Saved Profiles</h3><table class="table"><thead><tr><th>Profile</th><th>Autoconnect</th></tr></thead><tbody id="profileRows"></tbody></table></div></div></section>
<section class="section"><div class="section-title"><h2>Ethernet Manager</h2><span id="ethBadge" class="badge warn">checking</span></div><div class="grid-2"><div class="card"><h3>DHCP / Static IP</h3><div class="form-grid"><div class="input-wrap"><label>Static IP/CIDR</label><input id="ethIp" class="input" placeholder="192.168.1.50/24"></div><div class="input-wrap"><label>Gateway</label><input id="ethGw" class="input" placeholder="192.168.1.1"></div><div class="input-wrap"><label>DNS</label><input id="ethDns" class="input" value="8.8.8.8"></div></div><div class="btn-row"><button class="primary-btn" onclick="ethDhcp()">Use DHCP</button><button class="warn-btn" onclick="ethStatic()">Apply Static</button></div><div class="log" id="ethLog">Ready.</div></div><div class="card"><h3>Internet Test</h3><div class="btn-row"><button class="primary-btn" onclick="post('/api/test/default','netLog')">Test Default</button><button class="ghost-btn" onclick="post('/api/test/wwan','netLog')">Test wwan0 LTE</button><button class="warn-btn" onclick="post('/api/modem/restart','netLog')">Restart ModemManager</button><button class="ghost-btn" onclick="post('/api/modem/scan','netLog')">Scan Modem</button></div><div class="log" id="netLog">Ready.</div></div></div></section>
<section class="section"><div class="section-title"><h2>Power Control</h2><span class="badge warn">protected</span></div><div class="btn-row"><button class="danger-btn" onclick="confirmPost('/api/power/reboot','Reboot device now?')">Reboot</button><button class="danger-btn" onclick="confirmPost('/api/power/off','Power off device now?')">Power Off</button></div></section>
<section class="section"><div class="section-title"><h2>Diagnostics</h2><span class="badge ok">live</span></div><div class="grid-2"><div class="card"><h3>System</h3><pre id="sysPre">Loading...</pre></div><div class="card"><h3>HDMI / Storage</h3><pre id="devPre">Loading...</pre></div></div></section>
<div class="footer">Link2M · Arwito Tech · Industrial Gateway Hardware Center</div>
</main></div>
<script>
function $(id){return document.getElementById(id)}function b(ok,good='present',bad='not detected'){return `<span class="badge ${ok?'ok':'bad'}">${ok?good:bad}</span>`}function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}function row(k,v){return `<div class="row"><div class="k">${esc(k)}</div><div class="v">${v}</div></div>`}function setText(id,v){const e=$(id);if(e)e.textContent=v}function log(id,msg){const e=$(id||'netLog');if(e)e.textContent=typeof msg==='string'?msg:JSON.stringify(msg,null,2)}function scrollToSection(id){document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'start'})}
async function get(path){const r=await fetch(path,{cache:'no-store'});return await r.json()}async function post(path,logId,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):'{}'});const j=await r.json().catch(()=>({ok:false,err:'invalid response'}));log(logId||'netLog',j);setTimeout(refreshAll,1000);return j}function confirmPost(path,msg){if(confirm(msg))post(path,'netLog')}
function renderStatus(d){setText('mTemp',d.temperature_c?`${d.temperature_c} °C`:'-');setText('mEth',d.network.eth0.ip||'-');setText('mWlan',d.network.wlan0.ip||'-');setText('mWwan',d.network.wwan0.ip||'-');setText('sEth',`eth0 · ${d.network.eth0.state}`);setText('sWlan',`wlan0 · ${d.network.wlan0.state}`);setText('sWwan',`wwan0 · ${d.network.wwan0.state}`);setText('mUptime',d.uptime||'-');setText('mTime',d.time||'-');$('overall').className='badge ok';$('overall').textContent='online';const fan=d.fan||{};$('fanBadge').className='badge '+(fan.service==='active'?'ok':'bad');$('fanBadge').textContent=fan.service||'unknown';$('fanOn').value=fan.on_c||45;$('fanOff').value=fan.off_c||38;$('fanRows').innerHTML=row('Service',b(fan.service==='active','active','inactive'))+row('Device',esc(fan.device||'-'))+row('State',esc(`${fan.cur_state||0} / ${fan.max_state||1}`))+row('Threshold',esc(`ON ${fan.on_c||'-'} °C · OFF ${fan.off_c||'-'} °C`));const dev=d.devices||{};$('coreRows').innerHTML=row('Wi-Fi',b(dev.wifi?.present))+row('Bluetooth',b(dev.bluetooth?.present))+row('Modem USB',b(dev.modem?.usb_present))+row('USB Storage',b(dev.usb_storage?.present));$('storageRows').innerHTML=row('HDMI',b(dev.hdmi?.connected,'connected','not connected'))+row('Framebuffer',b(dev.hdmi?.fb,'available','missing'))+row('SD Card',b(dev.sd_card?.present,'present','not detected'));const sim=dev.modem?.sim||'unknown';$('modemRows').innerHTML=row('USB Node',b(dev.modem?.usb_present,'present','missing'))+row('ModemManager ID',esc(dev.modem?.modem_id||'-'))+row('SIM',`<span class="badge ${sim==='detected'?'ok':'warn'}">${esc(sim)}</span>`)+row('Nodes',esc((dev.modem?.nodes||[]).join(', ')||'-'));$('wifiBadge').className='badge '+(d.network.wlan0.ip!=='-'?'ok':'warn');$('wifiBadge').textContent=d.network.wlan0.ip!=='-'?'connected':'standby';$('ethBadge').className='badge '+(d.network.eth0.ip!=='-'?'ok':'warn');$('ethBadge').textContent=d.network.eth0.ip!=='-'?'connected':'standby';$('sysPre').textContent=JSON.stringify({loadavg:d.system.loadavg,memory:d.system.memory,disk:d.system.disk},null,2);$('devPre').textContent=JSON.stringify({hdmi:dev.hdmi,storage:dev.sd_card?.storage,modem:dev.modem?.mmcli_list},null,2)}
async function refreshAll(){try{const d=await get('/api/status');renderStatus(d);loadProfiles()}catch(e){$('overall').className='badge bad';$('overall').textContent='offline'}}async function scanWifi(){log('wifiLog','Scanning Wi-Fi...');const j=await get('/api/wifi/scan');const sel=$('ssid');sel.innerHTML='';(j.items||[]).forEach(x=>{if(!x.ssid)return;const opt=document.createElement('option');opt.value=x.ssid;opt.textContent=`${x.active?'● ':''}${x.ssid} · ${x.signal}% · ${x.security||'open'}`;sel.appendChild(opt)});log('wifiLog',j.items?.length?`Found ${j.items.length} Wi-Fi profile(s).`:(j.err||j.raw||'No Wi-Fi found.'))}
async function loadProfiles(){try{const j=await get('/api/wifi/profiles');$('profileRows').innerHTML=(j.items||[]).map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.autoconnect||'-')}</td></tr>`).join('')||'<tr><td colspan="2">No saved Wi-Fi profile</td></tr>'}catch(e){}}async function connectWifi(){await post('/api/wifi/connect','wifiLog',{ssid:$('ssid').value,password:$('wifiPass').value})}async function reconnectWifi(){await post('/api/wifi/reconnect','wifiLog')}async function forgetWifi(){await post('/api/wifi/forget','wifiLog',{name:$('ssid').value})}async function wifiAuto(enable){await post('/api/wifi/autoreconnect','wifiLog',{enable,name:$('ssid').value})}async function wifiKeepalive(enable){await post('/api/wifi/keepalive','wifiLog',{enable})}function togglePass(){const p=$('wifiPass');p.type=p.type==='password'?'text':'password'}async function ethDhcp(){await post('/api/eth/dhcp','ethLog')}async function ethStatic(){await post('/api/eth/static','ethLog',{ip:$('ethIp').value,gateway:$('ethGw').value,dns:$('ethDns').value})}async function saveFan(){await post('/api/fan/save','fanLog',{on_c:$('fanOn').value,off_c:$('fanOff').value})}refreshAll();scanWifi();setInterval(refreshAll,5000);
</script>
</body></html>
'''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

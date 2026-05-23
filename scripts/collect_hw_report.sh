#!/usr/bin/env bash
set +e

OUT="${1:-/root/link2m_hw_report_$(date +%F_%H%M%S).txt}"

{
echo "===== LINK2M KING3399 HARDWARE REPORT ====="
date
echo

echo "===== SYSTEM ====="
hostname
uname -a
cat /proc/device-tree/model 2>/dev/null
cat /etc/os-release 2>/dev/null
echo

echo "===== NETWORK ====="
ip a
ip route
cat /etc/resolv.conf
echo

echo "===== TEMPERATURE ====="
cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null
for c in /sys/class/thermal/cooling_device*; do
  echo "---- $c ----"
  cat "$c/type" 2>/dev/null
  cat "$c/max_state" 2>/dev/null
  cat "$c/cur_state" 2>/dev/null
done
echo

echo "===== SERVICES ====="
systemctl status ssh --no-pager
systemctl status NetworkManager --no-pager
systemctl status bluetooth --no-pager
systemctl status ModemManager --no-pager
systemctl status link2m-fan-hysteresis.service --no-pager
systemctl status king3399-web.service --no-pager
echo

echo "===== STORAGE ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
blkid
df -h
echo

echo "===== USB ====="
lsusb
lsusb -t
ls -l /dev/cdc-wdm* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
echo

echo "===== HDMI / DRM ====="
ls -l /sys/class/drm 2>/dev/null
cat /sys/class/drm/card*-HDMI-A-*/status 2>/dev/null
cat /sys/class/drm/card*-HDMI-A-*/modes 2>/dev/null
ls -l /dev/fb* 2>/dev/null
echo

echo "===== WIFI / BLUETOOTH ====="
rfkill list
nmcli dev status 2>/dev/null
nmcli -t -f NAME,TYPE,AUTOCONNECT con show 2>/dev/null
bluetoothctl list 2>/dev/null
echo

echo "===== MODEM ====="
mmcli -L 2>/dev/null
mmcli -m 0 2>/dev/null
lsmod | grep -Ei "cdc_mbim|qmi_wwan|option|usbserial|cdc_wdm" 2>/dev/null
echo

echo "===== DMESG TAIL ====="
dmesg | grep -Ei "usb|mmc|sdhci|dwmmc|hdmi|drm|rockchipdrm|vop|display|fan|gpio|cdc|mbim|qmi|wwan|ttyUSB|option|bluetooth|wifi|wlan" | tail -250
} > "$OUT" 2>&1

echo "Report saved to: $OUT"

# 03 - Hardware Validation Checklist

Gunakan checklist ini setelah board boot.

## LAN Ethernet

```bash
ip a show eth0
ip route
ping -c 3 8.8.8.8
```

## Wi-Fi

```bash
rfkill list
ip link show wlan0
nmcli dev wifi list ifname wlan0
```

Connect Wi-Fi:

```bash
nmcli dev wifi connect "SSID_WIFI" password "PASSWORD_WIFI" ifname wlan0
```

Reconnect:

```bash
nmcli dev disconnect wlan0
sleep 2
nmcli dev connect wlan0
```

Forget profile:

```bash
nmcli con delete "SSID_WIFI"
```

## Bluetooth

```bash
systemctl enable --now bluetooth
systemctl status bluetooth --no-pager
bluetoothctl list
rfkill list
```

Log `sap driver initialization failed` pada BlueZ umumnya tidak kritikal untuk fungsi Bluetooth dasar.

## HDMI

```bash
ls /sys/class/drm
cat /sys/class/drm/card*-HDMI-A-*/status 2>/dev/null
cat /sys/class/drm/card*-HDMI-A-*/modes 2>/dev/null
ls -l /dev/fb*
dmesg | grep -Ei "hdmi|drm|rockchipdrm|vop|display" | tail -100
```

Status bagus:

```text
connected
```

## SD Card

Masukkan SD card, lalu cek:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
dmesg | grep -Ei "mmc|sdhci|dwmmc" | tail -100
```

Mount test:

```bash
mkdir -p /mnt/sdtest
mount /dev/mmcblk1p1 /mnt/sdtest
df -h
ls -la /mnt/sdtest
```

## USB Storage

Masukkan flashdisk, lalu cek:

```bash
lsusb
lsusb -t
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
dmesg | grep -Ei "usb|xhci|ehci|uas|storage|sda|sdb" | tail -100
```

Mount test:

```bash
mkdir -p /mnt/usbtest
mount /dev/sda1 /mnt/usbtest
df -h
ls -la /mnt/usbtest
```

Jika `/dev/sda1` tidak ada, cek nama device dengan `lsblk`.

## LTE Modem Dell DW5821e Snapdragon X20

Cek device:

```bash
lsusb
ls -l /dev/cdc-wdm* /dev/ttyUSB* 2>/dev/null
lsmod | grep -Ei "cdc_mbim|qmi_wwan|option|usbserial|cdc_wdm"
```

Cek ModemManager:

```bash
systemctl restart ModemManager
sleep 10
mmcli -L
mmcli -m 0
```

Cek MBIM langsung:

```bash
systemctl stop ModemManager
sleep 2
mbimcli -d /dev/cdc-wdm0 --query-device-caps
mbimcli -d /dev/cdc-wdm0 --query-subscriber-ready-status
mbimcli -d /dev/cdc-wdm0 --query-radio-state
systemctl start ModemManager
```

Tanpa SIM, status seperti ini normal:

```text
sim-missing
+CME ERROR: 10
```

Itu bukan masalah antena. Antena baru berpengaruh saat mencari sinyal/operator setelah SIM terpasang.

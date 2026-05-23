# Link2M Hardware Center for KING3399 / RK3399 Gateway

![Link2M](web/static/link2m.svg)

**Link2M Hardware Center** is an open-source hardware bring-up, validation, and monitoring toolkit for **KING3399 / RK3399-based gateway boards**.

This repository documents the practical workflow used to bring up a KING3399 board, starting from Rockchip flashing preparation, Ophub/Armbian Ubuntu Noble image selection, first boot, DHCP/SSH access, hardware validation, fan hysteresis control, and deployment of the **Link2M web-based hardware monitoring dashboard**.

The purpose of this project is to help makers, engineers, and contributors avoid repeated trial-and-error when working with KING3399 / RK3399 gateway boards.

---

## What This Repository Is For

This repository is focused on:

- KING3399 / RK3399 board bring-up documentation.
- RKDevTool flashing workflow notes.
- Ophub / Armbian Ubuntu Noble image usage notes.
- RK3399 loader usage notes.
- First boot and DHCP-based SSH access.
- Hardware detection and validation.
- Fan hysteresis service for thermal control.
- Link2M web dashboard for hardware monitoring.
- Practical scripts used to check board devices and system health.

This repository is **not only an installation script repository**. The scripts are helper tools for hardware validation, fan control, and web dashboard deployment.

---

## External References

### Ophub / Armbian Image Source

Ubuntu Noble / Armbian images for RK3399-based devices can be obtained from the Ophub project:

```text
https://github.com/ophub/amlogic-s9xxx-armbian/releases/download/Armbian_noble_arm64_server_2026.05/Armbian_26.05.0_rockchip_king3399_noble_6.12.89_server_2026.05.15.img.gz
```

### RKDevTool / Rockchip Flash Tools

Rockchip flashing tools and instructions can be referenced from Radxa documentation:

```text
https://wiki.radxa.com/Rock3/install/rockchip-flash-tools
```

### RK3399 Loader

The RK3399 loader used during this project:

```text
https://github.com/Manssizz/flash-king3399/raw/refs/heads/main/rk3399_loader_v1.27.126.bin
```

---

## Important Flashing Notes

During flashing, the board must be detected by RKDevTool in Rockchip boot / loader mode.

The expected device status is similar to:

```text
Found One LOADER Device
```

For the tested KING3399 board, the **loader** and the **image** must be selected together during flashing.
<br>
<br>
<img width="1280" height="645" alt="6091264654215680041" src="https://github.com/user-attachments/assets/2b3002b3-9180-4f99-9b69-40287e061448" />

<br>


| Item | File Type | Example |
|---|---:|---|
| Loader | `.bin` | `rk3399_loader_v1.27.126.bin` |
| OS Image | `.img` | Ophub / Armbian Ubuntu Noble RK3399 image |

Recommended flashing flow:

1. Put the board into Rockchip boot / loader mode.
2. Open RKDevTool on Windows.
3. Confirm that RKDevTool detects the board.
4. Select the RK3399 loader file.
5. Select the Ophub / Armbian Ubuntu Noble image file.
6. Start flashing.
7. Wait until the image download process reaches 100%.
8. Reboot the board.
9. Wait for DHCP to assign an IP address.
10. Access the board using SSH.

> Note: This repository does not include `.img` and `.bin` firmware files because they are large and may differ by board revision.

---

## Tested Environment

| Component | Tested Status |
|---|---|
| Board | KING3399 / RK3399 gateway |
| OS | Armbian / Ubuntu Noble from Ophub-based image |
| Kernel | 6.12.x Ophub-based kernel |
| Architecture | aarch64 |
| Network | DHCP through Ethernet LAN |
| SSH | Working |
| Web Dashboard | Link2M Hardware Center |
| Dashboard Port | `8080` |

Example dashboard URL:

```text
http://192.168.1.15:8080
```

---

## First Boot and SSH Access

After flashing, connect the Ethernet cable and power on the board.

Find the assigned IP address from your router DHCP client list or with a network scanner.

Example using `nmap`:

```bash
nmap -sn 192.168.1.0/24
```

Then connect through SSH:

```bash
ssh root@192.168.1.15
```

Replace `192.168.1.15` with your actual board IP address.

---

## Hardware Validation Checklist

The following hardware features were checked or prepared for web monitoring:

| Feature | Purpose |
|---|---|
| Ethernet LAN | Main network and SSH access |
| Wi-Fi / WLAN | Wireless interface detection and future connection control |
| Bluetooth | Bluetooth controller and service status |
| HDMI | HDMI connector and display mode detection |
| SD Card | Storage detection and mount test |
| USB Host | USB device and hotplug detection |
| LTE Modem | DW5821e Snapdragon X20 LTE modem detection |
| WWAN | LTE network interface and modem status |
| Temperature | Thermal zone monitoring |
| Fan | GPIO fan hysteresis control |
| System Health | CPU load, memory, disk usage, uptime |
| Power Control | Reboot and power-off commands from dashboard |

---

## Fan Hysteresis Control

The tested board exposes the fan through the Linux thermal cooling device interface.

The detected fan device type was:

```text
/sys/class/thermal/cooling_device*/type = gpio-fan
```

The hysteresis controller uses two temperature thresholds:

| Setting | Description |
|---|---|
| `ON_TEMP` | Fan turns ON when the temperature reaches this value |
| `OFF_TEMP` | Fan turns OFF when the temperature drops below this value |

Example tested values:

```text
ON_TEMP=45000
OFF_TEMP=38000
```

Meaning:

- Fan ON at approximately **45 °C**.
- Fan OFF at approximately **38 °C**.

This prevents rapid fan ON/OFF switching and keeps the RK3399 temperature stable.

---

## Link2M Web Dashboard

The Link2M web dashboard provides a browser-based hardware monitoring center for KING3399 / RK3399 gateway boards.

<br>

<img width="2900" height="1617" alt="image" src="https://github.com/user-attachments/assets/d29bc452-3a66-4496-9084-bc1efe34bd4a" />

<br>
<br>

Current dashboard functions include:

- Temperature monitoring.
- Uptime monitoring.
- LAN IP address display.
- WLAN / Wi-Fi status display.
- WWAN / LTE modem status display.
- HDMI detection.
- SD card detection.
- USB device detection.
- Bluetooth status.
- ModemManager status.
- Fan hysteresis configuration.
- Reboot and power-off controls.
- Hardware summary section.
- Industrial-style web UI for gateway product presentation.

Default port:

```text
8080
```

Access example:

```text
http://<device-ip>:8080
```

---

## Repository Structure

```text
.
├── README.md
├── CHANGELOG.md
├── .gitignore
├── docs/
│   ├── 01-flashing-rkdevtool.md
│   ├── 02-first-boot-ssh-network.md
│   ├── 03-hardware-validation.md
│   ├── 04-fan-hysteresis.md
│   └── 05-web-dashboard.md
├── firmware/
│   └── README.md
├── scripts/
│   ├── collect_hw_report.sh
│   ├── install_fan_hysteresis.sh
│   ├── install_link2m_web_full.sh
│   └── install_prerequisites.sh
├── web/
│   ├── app.py
│   └── static/
│       └── link2m.svg
└── install_all.sh
```

---

## Firmware File Policy

Large firmware files are intentionally not included in this repository.

Do not commit files such as:

```text
*.img
*.bin
*.zip
*.7z
*.rar
```

Recommended local folder:

```text
firmware/
```

Example local-only files:

```text
firmware/rk3399_loader_v1.27.126.bin
firmware/Armbian_ubuntu_noble_rk3399.img
```

These files should remain local and should not be uploaded to GitHub.

---

## Quick Start After Flashing

After the board has booted and SSH access is available, install basic packages:

```bash
sudo apt update
sudo apt install -y git curl wget nano python3 python3-pip python3-flask net-tools usbutils pciutils lshw rfkill bluez modemmanager libmbim-utils libqmi-utils gpiod
```

Clone this repository:

```bash
git clone https://github.com/rezaistoni-cloud/King3399-Link2M-hardware-center.git
cd King3399-Link2M-hardware-center
```

Run hardware report:

```bash
sudo bash scripts/collect_hw_report.sh
```

Install fan hysteresis service:

```bash
sudo bash scripts/install_fan_hysteresis.sh
```

Install Link2M web dashboard:

```bash
sudo bash scripts/install_link2m_web_full.sh
```

Open the dashboard:

```text
http://<device-ip>:8080
```

---

## Development Status

Current status:

- RKDevTool flashing workflow documented.
- Ophub / Armbian Ubuntu Noble image tested.
- RK3399 loader workflow documented.
- Board boots successfully.
- DHCP LAN access confirmed.
- SSH access confirmed.
- Fan hysteresis service working.
- Basic hardware validation completed.
- Link2M web dashboard created and running.
- LTE modem detection confirmed.
- Wi-Fi, Bluetooth, HDMI, SD card, USB, and system health monitoring prepared.

Planned improvements:

- Wi-Fi scan and connect workflow.
- Wi-Fi forget and reconnect support.
- Ethernet DHCP / static IP configuration page.
- WWAN LTE connection workflow.
- Modem internet test.
- Improved device hotplug detection.
- More polished Link2M dashboard UI/UX.
- More board compatibility notes.

---

## Contributing

Contributions are welcome.

You can help by contributing:

- Board compatibility reports.
- RK3399 loader and image notes.
- Hardware test results.
- Dashboard UI improvements.
- Wi-Fi / LTE connection scripts.
- Documentation updates.
- Bug reports and fixes.

When opening an issue, please include:

- Board model.
- Image name and version.
- Kernel version.
- Boot storage type.
- Hardware test result.
- Relevant logs or screenshots.

---

## Disclaimer

Flashing and low-level hardware operations can permanently modify the board storage.

Please verify the correct image, loader, board mode, and power stability before flashing.

Use this repository as a practical engineering reference and validate all steps on your own hardware revision before production use.

---

## License

This project is released as an open-source toolkit for KING3399 / RK3399 gateway bring-up, validation, and monitoring.

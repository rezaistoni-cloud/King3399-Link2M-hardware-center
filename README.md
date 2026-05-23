# KING3399 Link2M Hardware Center

Repository ini berisi dokumentasi dan script instalasi untuk **RK KING3399 / RK3399 gateway** sampai tahap berhasil menjalankan **Link2M Hardware Center** berbasis web.

Target akhir:

- Board berhasil di-flash memakai image Ubuntu Noble dari Ophub/Armbian.
- Boot normal, dapat IP dari DHCP.
- SSH aktif.
- Fan hysteresis aktif.
- Hardware dasar terdeteksi: LAN, Wi-Fi, Bluetooth, HDMI, SD card, USB, modem LTE.
- Web monitoring berjalan di port `8080`.

> Catatan penting: repository ini **tidak menyertakan file image `.img` dan loader `.bin`** karena ukuran besar dan bisa berbeda per board. Simpan file tersebut di folder `firmware/` secara lokal.

---

## Struktur Repository

```text
KING3399-Link2M-Hardware-Center/
├── README.md
├── CHANGELOG.md
├── firmware/
│   └── README.md
├── docs/
│   ├── 01-flashing-rkdevtool.md
│   ├── 02-first-boot-ssh-network.md
│   ├── 03-hardware-validation.md
│   ├── 04-fan-hysteresis.md
│   └── 05-web-dashboard.md
├── scripts/
│   ├── install_prerequisites.sh
│   ├── install_link2m_web_full.sh
│   ├── install_fan_hysteresis.sh
│   └── collect_hw_report.sh
└── web/
    ├── app.py
    └── static/
        └── link2m.svg
```

---

## Quick Start Setelah Flashing

Masuk SSH ke board:

```bash
ssh root@192.168.1.15
```

Upload repository ini ke board, lalu jalankan:

```bash
cd KING3399-Link2M-Hardware-Center

bash scripts/install_prerequisites.sh
bash scripts/install_fan_hysteresis.sh
bash scripts/install_link2m_web_full.sh
```

Buka dari browser:

```text
http://192.168.1.15:8080
```

Ganti `192.168.1.15` sesuai IP board Bapak.

---

## Status Saat Ini

Versi ini dibuat berdasarkan proses instalasi yang sudah berhasil:

- Image Ubuntu Noble berhasil flash ke KING3399.
- RKDevTool berhasil download image sampai `Download image OK`.
- SSH berhasil masuk.
- Fan hysteresis dibuat dengan batas default:
  - Fan ON: `45 °C`
  - Fan OFF: `38 °C`
- Dashboard web Link2M sudah dibuat sebagai `web/app.py`.

---

## Prinsip Penting Saat Flashing

Saat memakai RKDevTool, jangan hanya memasukkan image atau loader secara terpisah. Pada kasus KING3399 ini, proses yang berhasil adalah:

1. Device harus masuk mode Rockchip flash, status RKDevTool:
   - `Found One LOADER Device`
   - atau mode sejenis Rockchip flash device.
2. Jangan flash ketika status masih:
   - `Found One ADB Device`
3. Pada tab **Download Image**, masukkan **loader dan image bersamaan**:
   - Row 1: `loader`, address `0x00000000`, file `rk3399_loader_v1.27.126.bin`
   - Row 2: `image`, address `0x00000000`, file Ubuntu Noble `.img`
4. Centang dua row tersebut.
5. Centang **Write by Address**.
6. Klik **Run**.
7. Log sukses yang diharapkan:
   - `Test Device Success`
   - `Check Chip Success`
   - `Download IDB Success`
   - `Wait For Loader Success`
   - `Start to download ...`
   - `Download image OK`

Jika setelah sukses status menjadi `No Devices Found`, itu normal karena board reboot.

---

## Troubleshooting Cepat

### RKDevTool menampilkan ADB device

Artinya board masih boot normal Android/Linux lama, bukan mode flash. Ulangi prosedur reset/boot/maskrom sampai status berubah ke LOADER/MASKROM.

### `Creating image object failed`

Biasanya path image bermasalah, file corrupt, atau RKDevTool tidak cocok dengan cara input. Gunakan path sederhana seperti:

```text
C:\Linux\king3399.img
C:\Linux\rk3399_loader_v1.27.126.bin
```

### `Match device type failed`

Biasanya loader tidak cocok, image/loader dimasukkan di menu yang salah, atau memakai tab/fitur RKDevTool yang bukan untuk raw image. Untuk workflow ini gunakan **Download Image**.

### Modem terdeteksi tetapi `sim-missing`

Itu normal kalau SIM belum dipasang. Antena tidak menyebabkan status SIM hilang. Antena berpengaruh ke sinyal setelah SIM terpasang dan modem register jaringan.

---

## Lisensi

Script dan dashboard dalam repository ini boleh dipakai dan dimodifikasi untuk project internal/komersial Arwito Tech.

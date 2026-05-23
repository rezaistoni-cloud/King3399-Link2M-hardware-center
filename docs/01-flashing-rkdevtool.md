# 01 - Flashing KING3399 dengan RKDevTool

Dokumen ini menjelaskan workflow flashing yang sudah berhasil dipakai pada KING3399.

## File yang dibutuhkan

Siapkan di Windows, contoh folder:

```text
C:\Linux\
├── RKDevTool_Release_v2.86\
├── rk3399_loader_v1.27.126.bin
└── king3399.img
```

Image `king3399.img` adalah image Ubuntu Noble/Armbian dari Ophub yang sudah diekstrak.

## Masuk mode Rockchip flash

Target status di RKDevTool:

```text
Found One LOADER Device
```

Status ini yang dipakai saat proses berhasil.

Jangan lanjut flash kalau status masih:

```text
Found One ADB Device
```

ADB berarti board masih boot OS normal, bukan mode loader/maskrom.

## Konfigurasi RKDevTool

Buka RKDevTool sebagai Administrator.

Masuk tab:

```text
Download Image
```

Isi row seperti berikut:

| Row | Address | Name   | Path |
|---:|---|---|---|
| 1 | `0x00000000` | `loader` | `C:\Linux\rk3399_loader_v1.27.126.bin` |
| 2 | `0x00000000` | `image` | `C:\Linux\king3399.img` |

Checklist:

- Centang row `loader`
- Centang row `image`
- Centang `Write by Address`

Lalu klik:

```text
Run
```

## Log sukses yang diharapkan

```text
Test Device Start
Test Device Success
Check Chip Start
Check Chip Success
Get FlashInfo Start
Get FlashInfo Success
Prepare IDB Start
Prepare IDB Success
Download IDB Start
Download IDB Success
Wait For Loader Start
Wait For Loader Success
Test Device Start
Test Device Success
Start to download king3399...
Download king3399... (100%)
Download image OK
```

Setelah selesai, status bisa berubah menjadi:

```text
No Devices Found
```

Itu normal karena board reboot.

## Error umum

### Found One ADB Device

Solusi:

- Ulangi tombol reset/boot/maskrom sesuai hardware.
- Pastikan kabel USB data bagus.
- Pastikan driver Rockchip sudah terpasang.
- Jangan lanjut flashing dalam status ADB.

### Creating image object failed

Solusi:

- Rename file image menjadi nama pendek, misalnya `king3399.img`.
- Taruh di path sederhana, misalnya `C:\Linux\king3399.img`.
- Pastikan image sudah diekstrak, bukan `.zip`/`.7z`.
- Coba jalankan RKDevTool sebagai Administrator.

### Match device type failed

Solusi:

- Jangan memakai menu Advanced Function untuk raw image ini.
- Gunakan tab `Download Image`.
- Masukkan `loader` dan `image` bersamaan.
- Pastikan loader cocok untuk RK3399.

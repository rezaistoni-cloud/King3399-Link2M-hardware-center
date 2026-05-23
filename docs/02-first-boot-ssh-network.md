# 02 - First Boot, DHCP, dan SSH

Setelah flashing selesai, board akan boot ke Ubuntu Noble/Armbian.

## Cari IP DHCP

Dari PC Windows bisa scan jaringan:

```powershell
nmap -p 22,80,8080 192.168.1.0/24
```

Atau lihat DHCP client list di router.

Pada proses yang sudah berhasil, board mendapat IP:

```text
192.168.1.15
```

## SSH

Masuk SSH:

```bash
ssh root@192.168.1.15
```

Setelah masuk, cek sistem:

```bash
hostname
uname -a
cat /proc/device-tree/model
ip a
df -h
free -h
cat /sys/class/thermal/thermal_zone*/temp
systemctl status ssh --no-pager
```

## Set hostname

Opsional:

```bash
hostnamectl set-hostname king3399-gateway
```

## Update package index

```bash
apt update
```

Lalu lanjut ke install dependency:

```bash
bash scripts/install_prerequisites.sh
```

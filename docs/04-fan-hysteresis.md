# 04 - Fan Hysteresis

Fan GPIO pada image ini dikenali sebagai thermal cooling device bertipe:

```text
gpio-fan
```

Cek:

```bash
for c in /sys/class/thermal/cooling_device*; do
  echo "---- $c ----"
  cat "$c/type" 2>/dev/null
  cat "$c/max_state" 2>/dev/null
  cat "$c/cur_state" 2>/dev/null
done
```

Install service hysteresis:

```bash
bash scripts/install_fan_hysteresis.sh
```

Default:

```text
ON_TEMP=45000   # 45 °C
OFF_TEMP=38000  # 38 °C
```

Cek service:

```bash
systemctl status link2m-fan-hysteresis.service --no-pager
cat /sys/class/thermal/cooling_device*/type
cat /sys/class/thermal/cooling_device*/cur_state
cat /sys/class/thermal/thermal_zone*/temp
```

## Mengubah nilai

Bisa melalui web dashboard, atau edit manual:

```bash
nano /usr/local/sbin/link2m-fan-hysteresis.sh
systemctl restart link2m-fan-hysteresis.service
```

Rekomendasi awal untuk gateway:

```text
ON  = 45 °C
OFF = 38 °C
```

Jika ingin fan lebih sering diam:

```text
ON  = 50 °C
OFF = 42 °C
```

Jika ingin CPU lebih dingin:

```text
ON  = 42 °C
OFF = 36 °C
```

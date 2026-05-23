#!/usr/bin/env bash
set -e

export DEBIAN_FRONTEND=noninteractive

apt update

apt install -y \
  python3 \
  python3-flask \
  network-manager \
  modemmanager \
  libmbim-utils \
  libqmi-utils \
  usbutils \
  pciutils \
  rfkill \
  iw \
  wireless-tools \
  bluez \
  gpiod \
  net-tools \
  curl \
  wget \
  nano \
  htop \
  lsof \
  util-linux

systemctl enable --now ssh || true
systemctl enable --now NetworkManager || true
systemctl enable --now bluetooth || true
systemctl enable --now ModemManager || true

echo "OK: prerequisites installed."

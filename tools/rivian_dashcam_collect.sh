#!/usr/bin/env bash
set -euo pipefail

HOST=${1:-comma@192.168.148.4}
OUTPUT_DIR=${2:-rivian-dashcam-capture-$(date +%Y%m%d-%H%M%S)}
SSH_CONFIG=${COMMA_SSH_CONFIG:-$HOME/.ssh/config}
SSH=(ssh -F "$SSH_CONFIG" -o BatchMode=yes -o ConnectTimeout=10 "$HOST")

mkdir -p "$OUTPUT_DIR/logs" "$OUTPUT_DIR/params"

"${SSH[@]}" '
  echo "== identity =="
  hostname
  date --iso-8601=seconds
  uptime
  git -C /data/openpilot log -1 --oneline --decorate 2>/dev/null || true
  git -C /data/openpilot status --short --branch 2>/dev/null || true
  echo "== processes =="
  ps -A -o pid,ppid,stat,etime,args
  echo "== USB topology =="
  lsusb -t 2>&1 || true
  lsusb 2>&1 || true
  echo "== USB sysfs =="
  for device in /sys/bus/usb/devices/*; do
    test -f "$device/idVendor" || continue
    printf "%s vid=" "$device"
    cat "$device/idVendor"
    printf " pid="
    cat "$device/idProduct"
    for field in busnum devnum devpath speed serial product manufacturer; do
      test -f "$device/$field" && { printf " %s=" "$field"; cat "$device/$field"; }
    done
  done
  echo "== kernel transport events =="
  dmesg -T 2>/dev/null | grep -Ei "usb|xhci|spi|disconnect|reset|descriptor|enumerat|error -71|error -110|error -32" || true
  echo "== journal transport/startup events =="
  journalctl --no-pager -b 2>/dev/null | grep -Ei "pandad|panda|spi|usb|fingerprint|dashcam|car\.passive" || true
' > "$OUTPUT_DIR/system-state.txt"

for key in CarParams CarParamsCache CarParamsPersistent CarParamsPrevRoute CarParamsSP CarParamsSPPersistent CurrentRoute GitBranch GitCommit GitDiff Version; do
  if "${SSH[@]}" "test -f /data/params/d/$key"; then
    "${SSH[@]}" "dd if=/data/params/d/$key status=none" > "$OUTPUT_DIR/params/$key"
  fi
done

mapfile -t LOG_FILES < <("${SSH[@]}" \
  'find /data/media/0/realdata -maxdepth 2 -type f \( -name "rlog*" -o -name "qlog*" \) -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -24 | cut -d" " -f2-')
for remote_file in "${LOG_FILES[@]}"; do
  route_segment=$(basename "$(dirname "$remote_file")")
  mkdir -p "$OUTPUT_DIR/logs/$route_segment"
  "${SSH[@]}" "dd if='$remote_file' status=none" > "$OUTPUT_DIR/logs/$route_segment/$(basename "$remote_file")"
done

mapfile -t BOOT_FILES < <("${SSH[@]}" \
  'find /data -type f \( -name "bootlog*" -o -path "*/boot/*" \) -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -10 | cut -d" " -f2-')
printf '%s\n' "${BOOT_FILES[@]}" > "$OUTPUT_DIR/bootlog-inventory.txt"
mkdir -p "$OUTPUT_DIR/bootlogs"
for remote_file in "${BOOT_FILES[@]}"; do
  test -n "$remote_file" || continue
  local_name=$(printf '%s' "$remote_file" | tr '/' '_')
  "${SSH[@]}" "dd if='$remote_file' status=none" > "$OUTPUT_DIR/bootlogs/$local_name"
done

find "$OUTPUT_DIR" -type f -printf '%s %p\n' | sort > "$OUTPUT_DIR/manifest.txt"
echo "Capture written to $OUTPUT_DIR"
echo "Do not reboot the comma or let the vehicle sleep until this initial-failure capture is complete."

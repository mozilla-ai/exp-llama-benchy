#!/bin/sh
# Sample the Steam Deck's thermal / clock / load state during a benchmark so a
# suspicious cell can be checked against the machine's actual state instead of
# inferred from throughput. Timestamps are ISO-8601 UTC, matching the timestamp
# field in llama-benchy's result JSON, so rows join to cells directly.
#
#   usage: tools/deck-telemetry.sh [INTERVAL_S] > logs/telemetry.csv
#
# Columns: ts, gpu_edge_c, cpu_c, batt_c, fan_rpm, gpu_busy_pct, sclk, cpu_mhz_max, load1
set -u
INT="${1:-2}"
AMD=$(dirname "$(grep -l '^amdgpu$' /sys/class/hwmon/*/name 2>/dev/null | head -1)")
SDH=$(dirname "$(grep -l '^steamdeck_hwmon$' /sys/class/hwmon/*/name 2>/dev/null | head -1)")
ACPI=$(dirname "$(grep -l '^acpitz$' /sys/class/hwmon/*/name 2>/dev/null | head -1)")
BUSY=$(ls /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null | head -1)
SCLK=$(ls /sys/class/drm/card*/device/pp_dpm_sclk 2>/dev/null | head -1)
r() { cat "$1" 2>/dev/null || echo ""; }
mC() { v=$(r "$1"); [ -n "$v" ] && echo $((v/1000)) || echo ""; }
echo "ts,gpu_edge_c,cpu_c,batt_c,fan_rpm,gpu_busy_pct,sclk,cpu_mhz_max,load1"
while :; do
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$(mC "$AMD/temp1_input")" \
    "$(mC "$ACPI/temp1_input")" \
    "$(mC "$SDH/temp1_input")" \
    "$(r "$SDH/fan1_input")" \
    "$(r "$BUSY")" \
    "$(sed -n 's/.*: \([0-9]*\)Mhz \*/\1/p' "$SCLK" 2>/dev/null | head -1)" \
    "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null | sort -n | tail -1 | awk '{print int($1/1000)}')" \
    "$(awk '{print $1}' /proc/loadavg)"
  sleep "$INT"
done

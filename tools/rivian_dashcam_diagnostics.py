#!/usr/bin/env python3
"""Summarize transport, CAN, fingerprint, and dashcam evidence from route logs."""

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openpilot.tools.lib.logreader import LogReader, ReadMode


CRITICAL_IDS = {0x1310: "angle_upgrade", 0x131A: "longitudinal_upgrade"}
DIAGNOSTIC_LOG_TERMS = (
  "rivian_startup_diagnostic", "car.passive_decision", "pandad.discovery", "fingerprinted",
  "spi:", "panda usb", "protocol_mismatch", "pandad.uncaught_exception",
)


def enum_name(value: Any) -> str:
  return str(value).split(".")[-1]


@dataclass
class BusStats:
  frame_count: int = 0
  first_time: float | None = None
  last_time: float | None = None
  longest_gap: float = 0.0
  addresses: Counter[int] = field(default_factory=Counter)
  first_payload: dict[int, bytes] = field(default_factory=dict)
  changing_addresses: set[int] = field(default_factory=set)
  critical_first_time: dict[int, float] = field(default_factory=dict)

  def add(self, timestamp: float, address: int, payload: bytes) -> None:
    if self.first_time is None:
      self.first_time = timestamp
    if self.last_time is not None:
      self.longest_gap = max(self.longest_gap, timestamp - self.last_time)
    self.last_time = timestamp
    self.frame_count += 1
    self.addresses[address] += 1
    if address not in self.first_payload:
      self.first_payload[address] = payload
    elif self.first_payload[address] != payload:
      self.changing_addresses.add(address)
    if address in CRITICAL_IDS and address not in self.critical_first_time:
      self.critical_first_time[address] = timestamp

  def as_dict(self, origin: float) -> dict[str, Any]:
    duration = 0.0 if self.first_time is None or self.last_time is None else self.last_time - self.first_time
    static = set(self.addresses) - self.changing_addresses
    return {
      "frame_count": self.frame_count,
      "frames_per_second": self.frame_count / duration if duration > 0 else 0.0,
      "unique_address_count": len(self.addresses),
      "first_time_s": None if self.first_time is None else self.first_time - origin,
      "last_time_s": None if self.last_time is None else self.last_time - origin,
      "longest_receive_gap_s": self.longest_gap,
      "changing_addresses": [f"0x{x:x}" for x in sorted(self.changing_addresses)],
      "static_addresses": [f"0x{x:x}" for x in sorted(static)],
      "critical_ids": {
        f"0x{address:x}": {
          "name": name,
          "present": address in self.addresses,
          "frame_count": self.addresses[address],
          "first_time_s": self.critical_first_time.get(address, origin) - origin if address in self.critical_first_time else None,
        }
        for address, name in CRITICAL_IDS.items()
      },
    }


def car_params_dict(cp: Any) -> dict[str, Any]:
  return {
    "car_fingerprint": cp.carFingerprint,
    "brand": cp.brand,
    "fingerprint_source": enum_name(cp.fingerprintSource),
    "fuzzy_fingerprint": cp.fuzzyFingerprint,
    "dashcam_only": cp.dashcamOnly,
    "passive": cp.passive,
    "safety_configs": [
      {"safety_model": enum_name(config.safetyModel), "safety_param": config.safetyParam}
      for config in cp.safetyConfigs
    ],
  }


def can_state_dict(state: Any) -> dict[str, Any]:
  return {
    "bus_off": state.busOff,
    "bus_off_count": state.busOffCnt,
    "error_warning": state.errorWarning,
    "error_passive": state.errorPassive,
    "receive_error_count": state.receiveErrorCnt,
    "transmit_error_count": state.transmitErrorCnt,
    "total_error_count": state.totalErrorCnt,
    "total_rx_lost_count": state.totalRxLostCnt,
    "total_tx_lost_count": state.totalTxLostCnt,
    "total_rx_count": state.totalRxCnt,
    "total_tx_count": state.totalTxCnt,
    "can_core_reset_count": state.canCoreResetCnt,
    "last_error": enum_name(state.lastError),
  }


def panda_state_dict(state: Any) -> dict[str, Any]:
  return {
    "panda_type": enum_name(state.pandaType),
    "uptime": state.uptime,
    "ignition_line": state.ignitionLine,
    "ignition_can": state.ignitionCan,
    "harness_status": enum_name(state.harnessStatus),
    "safety_model": enum_name(state.safetyModel),
    "safety_param": state.safetyParam,
    "fault_status": enum_name(state.faultStatus),
    "faults": [enum_name(fault) for fault in state.faults],
    "heartbeat_lost": state.heartbeatLost,
    "spi_error_count": state.spiErrorCount,
    "rx_buffer_overflow": state.rxBufferOverflow,
    "tx_buffer_overflow": state.txBufferOverflow,
    "can_states": [can_state_dict(getattr(state, f"canState{bus}")) for bus in range(3)],
  }


def analyze(messages: Any, source: str = "") -> dict[str, Any]:
  buses: dict[int, BusStats] = {}
  origin: float | None = None
  car_params: dict[str, Any] | None = None
  panda_states: list[dict[str, Any]] = []
  spi_error_range: list[int] = []
  diagnostic_logs: list[dict[str, Any]] = []
  message_counts: Counter[str] = Counter()

  for msg in messages:
    timestamp = msg.logMonoTime / 1e9
    origin = timestamp if origin is None else min(origin, timestamp)
    msg_type = msg.which()
    message_counts[msg_type] += 1

    if msg_type == "can":
      for frame in msg.can:
        buses.setdefault(frame.src, BusStats()).add(timestamp, frame.address, bytes(frame.dat))
    elif msg_type == "carParams":
      car_params = car_params_dict(msg.carParams)
    elif msg_type == "pandaStates":
      panda_states = [panda_state_dict(state) for state in msg.pandaStates]
      spi_error_range.extend(state.spiErrorCount for state in msg.pandaStates)
    elif msg_type in ("logMessage", "errorLogMessage"):
      text = str(getattr(msg, msg_type))
      text_lower = text.lower()
      routine_spi_retry = "spi:" in text_lower and ("got nack" in text_lower or "nack sleep" in text_lower)
      if not routine_spi_retry and any(term in text_lower for term in DIAGNOSTIC_LOG_TERMS):
        diagnostic_logs.append({"time_s": timestamp, "type": msg_type, "text": text})

  origin = origin or 0.0
  for entry in diagnostic_logs:
    entry["time_s"] -= origin

  return {
    "source": source,
    "log_origin_mono_time_s": origin,
    "message_counts": dict(sorted(message_counts.items())),
    "car_params": car_params,
    "panda_states_latest": panda_states,
    "panda_spi_error_count_range": {
      "first": spi_error_range[0] if spi_error_range else None,
      "last": spi_error_range[-1] if spi_error_range else None,
      "minimum": min(spi_error_range) if spi_error_range else None,
      "maximum": max(spi_error_range) if spi_error_range else None,
    },
    "can_buses": {str(bus): stats.as_dict(origin) for bus, stats in sorted(buses.items())},
    "diagnostic_logs": diagnostic_logs,
    "limitations": [
      "CAN rates and gaps are authoritative only with full rlog input; qlog CAN is heavily decimated.",
      "Panda spiErrorCount does not include every host-side ACK timeout, ioctl failure, or receive checksum error.",
    ],
  }


def render_text(report: dict[str, Any]) -> str:
  lines = [f"Source: {report['source']}"]
  cp = report["car_params"]
  if cp is None:
    lines.append("CarParams: not present")
  else:
    car_line = f"CarParams: {cp['car_fingerprint']} source={cp['fingerprint_source']} "
    car_line += f"dashcamOnly={cp['dashcam_only']} passive={cp['passive']}"
    lines.append(car_line)
  spi = report["panda_spi_error_count_range"]
  lines.append(f"Panda SPI errors: first={spi['first']} last={spi['last']} min={spi['minimum']} max={spi['maximum']}")
  lines.append("CAN buses:")
  for bus, stats in report["can_buses"].items():
    critical = stats["critical_ids"]
    bus_line = f"  bus {bus}: {stats['frame_count']} frames, {stats['frames_per_second']:.1f} fps, "
    bus_line += f"{stats['unique_address_count']} IDs, max_gap={stats['longest_receive_gap_s']:.3f}s, "
    bus_line += f"0x1310={critical['0x1310']['present']} ({critical['0x1310']['frame_count']}), "
    bus_line += f"0x131a={critical['0x131a']['present']} ({critical['0x131a']['frame_count']})"
    lines.append(bus_line)
  if report["diagnostic_logs"]:
    lines.append("Diagnostic log events:")
    lines.extend(f"  +{event['time_s']:.3f}s {event['type']}: {event['text']}" for event in report["diagnostic_logs"])
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("logs", nargs="+", help="rlog/qlog files, route names, or segment ranges")
  parser.add_argument("--json", metavar="PATH", help="also write the complete report as JSON; use - for JSON-only stdout")
  args = parser.parse_args()

  report = analyze(LogReader(args.logs, default_mode=ReadMode.RLOG, sort_by_time=True), ",".join(args.logs))
  if args.json == "-":
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print(render_text(report))
    if args.json:
      Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
  main()

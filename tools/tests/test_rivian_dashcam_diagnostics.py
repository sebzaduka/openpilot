from types import SimpleNamespace

from tools.rivian_dashcam_diagnostics import analyze


class CanEvent:
  def __init__(self, timestamp_s, frames):
    self.logMonoTime = int(timestamp_s * 1e9)
    self.can = [SimpleNamespace(src=bus, address=address, dat=data) for bus, address, data in frames]

  @staticmethod
  def which():
    return "can"


class LogEvent:
  def __init__(self, timestamp_s, text):
    self.logMonoTime = int(timestamp_s * 1e9)
    self.logMessage = text

  @staticmethod
  def which():
    return "logMessage"


def test_can_startup_characterization():
  messages = [
    CanEvent(10.0, [(0, 0x100, b"\x00"), (1, 0x1310, b"\x00")]),
    CanEvent(10.1, [(0, 0x100, b"\x01"), (1, 0x1310, b"\x00")]),
    CanEvent(10.6, [(1, 0x131A, b"\x00")]),
  ]
  report = analyze(messages, "synthetic")

  assert report["can_buses"]["0"]["changing_addresses"] == ["0x100"]
  assert report["can_buses"]["1"]["critical_ids"]["0x1310"]["frame_count"] == 2
  assert report["can_buses"]["1"]["critical_ids"]["0x131a"]["present"]
  assert report["can_buses"]["1"]["longest_receive_gap_s"] == 0.5


def test_missing_critical_id_and_bus():
  missing_id = analyze([CanEvent(1.0, [(1, 0x200, b"\x00")])])
  assert not missing_id["can_buses"]["1"]["critical_ids"]["0x1310"]["present"]

  missing_bus = analyze([CanEvent(1.0, [(0, 0x100, b"\x00")])])
  assert "1" not in missing_bus["can_buses"]


def test_routine_spi_nacks_are_not_highlighted():
  report = analyze([
    LogEvent(1.0, "SPI: got NACK, waiting for 0x85"),
    LogEvent(2.0, "SPI: bad checksum"),
  ])
  assert [event["text"] for event in report["diagnostic_logs"]] == ["SPI: bad checksum"]

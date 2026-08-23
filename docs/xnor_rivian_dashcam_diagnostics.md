# XNOR Rivian intermittent dashcam diagnostics

This document describes the behavior at source commit `0efff7d71`, deployed by prebuilt tag
`prebuilts/sbz-src/0efff7d710af6101214d47648e3057a3820b14b6`. It distinguishes an observed UI
"dashcam mode" from the narrower Rivian `dashcamOnly` decision.

## Root-cause map

```text
internal panda discovered over SPI (/dev/spidev0.0)
  | no panda/CAN -> startup waits; this is not itself the Rivian dashcam gate
  v
pandad publishes CAN + pandaStates
  | transport loss -> empty/invalid CAN, SPI logs/counter, possible CAN overflow
  v
VIN/FW query, then fresh CAN fingerprint (bus 0 and bus 1, normally 1-2 s)
  | no supported match -> MOCK -> dashcamOnly
  v
Rivian CarInterface._get_params
  | bus 1 lacks 0x1310 -> dashcamOnly = true
  v
card final policy
  | dashcamOnly OR no controller OR OpenpilotEnabledToggle off -> passive = true
  v
passive -> safetyConfigs replaced with noOutput -> UI dashcamMode event
```

For a car that reached the Rivian interface, the only Rivian-specific `dashcamOnly` assignment is
absence of `0x1310` from the **fresh logical-bus-1 fingerprint**. The visible dashcam event is not
proof of that path: an unrecognized car, missing controller, or disabled Openpilot toggle also makes
`CarParams.passive` true. A fault route is required to determine which occurred.

The decision is sticky for the lifetime of `card` because `CarParams` is constructed once. It is not
re-evaluated when `0x1310` appears later. A manager/comma restart constructs it again.

## Identification and initialization

`pandad.py` resets or recovers the internal panda, handles DFU devices, discovers pandas, optionally
checks/flashes XNOR's external black-panda longitudinal module, selects the supported internal panda,
and starts native `pandad`. Native `pandad` uses `PandaSpiHandle`; comma four production CAN traffic
does not travel through libusb.

`card.py` waits for a non-empty CAN publication, loads only the current-manager `CarParamsCache`, and
calls `get_car`. Identification performs VIN/firmware queries (possibly using the current cache),
drains CAN, then creates a fresh CAN fingerprint. CAN candidates are tested on buses 0 and 1. The
loop succeeds after one candidate remains and at least 100 received CAN batches, or fails after about
200 batches. Rivian may also be selected by firmware or a fixed platform, but its interface still
receives the fresh CAN fingerprint used by the `0x1310` gate.

Rivian configuration then:

- marks GEN2 when `0x321` is absent on bus 0;
- marks dashcam-only when `0x1310` is absent on bus 1;
- marks the longitudinal harness upgrade when `0x131a` is present on bus 1;
- initially selects Rivian safety, after which `card` replaces it with `noOutput` if passive.

Safety initialization failure is not a separate code path that sets Rivian dashcam-only. It can
prevent engagement or create faults after `CarParams` selection, but it does not explain this exact
boolean without another passive cause.

## SPI and USB assessment

### Internal panda SPI

Native CAN reads use SPI endpoint `0x81`. SPI transfers have checksums and retry NACK/ACK-timeout
failures. A terminal bulk failure marks host communications unhealthy; `pandad` publishes an invalid
CAN event with no frames. Temporary delay can backlog the panda's CAN queue; sustained delay can
produce receive-buffer overflow and lost frames.

SPI faults can therefore cause a missing `0x1310`, but normally they should affect multiple messages
or buses. Normal bus-1 traffic with only Extreme Dev Kit IDs absent points more strongly to the kit,
harness/routing, or vehicle-side state. Relevant evidence is:

- `pandaStates.spiErrorCount` (panda-detected malformed SPI transactions);
- host `SPI:` log errors (ACK timeouts, ioctl failures, bad receive checksums);
- `rxBufferOverflow`, raw-CAN gaps, and per-bus panda CAN loss/error counters.

No single existing counter covers every host- and panda-side SPI error.

### External USB

Python panda discovery uses libusb and catches setup-time `USBErrorNoDevice` and `USBErrorPipe`.
XNOR's external black panda is considered for custom firmware checking/flashing, but the supported
internal panda is selected for native `pandad`. Generic libusb operations otherwise propagate typed
exceptions; there are no continuous production counters for timeout, I/O, pipe, no-device, resets,
or reconnects. The diagnostic patch logs each discovery attempt and categorized exception.

Literal USB BER, PHY signal quality, CRC retry counts, and eye measurements are not exposed by this
application or the ordinary comma four USB sysfs interface. Useful proxies are device presence,
VID/PID/serial, topology, negotiated speed, enumeration/reset/disconnect kernel messages, libusb
errors, and discovery/reconnect history. These do not measure the CAN conductors carried through a
USB-C-shaped vehicle connector.

## Existing telemetry

| Signal | Logged | Location | Value for this fault |
|---|---:|---|---|
| Raw CAN | rlog; only about 3 batches/segment in qlog | `can` | Required for rates, gaps, bus mapping, and `0x1310` proof |
| Fingerprint details | rlog; original error event also qlog | `errorLogMessage` | Candidate/source, complete startup address sets, FW/VIN result |
| Final car configuration | rlog and qlog | `carParams` every 50 s | Platform, source, passive, dashcam-only, safety |
| Panda health | rlog and qlog at 10 Hz | `pandaStates` | SPI errors, faults, ignition, harness, buffer overflow, CAN health |
| Peripheral health | rlog and qlog | `peripheralState`, `deviceState` | Panda type, voltage/current, device health |
| Manager state | rlog and qlog | `managerState` | Process crashes/restarts |
| Host SPI/libusb errors | boot/swag logs; error-level events in qlog | `errorLogMessage`, boot logs | Direct transport evidence |
| Kernel USB events | journald/dmesg, not reliably in route logs | kernel journal | Enumeration, speed, reset, disconnect |
| USB BER/PHY counters | No | — | Use transport proxies above |
| Explicit reasons added here | qlog and rlog | `rivian_startup_diagnostic`, `car.passive_decision`, `pandad.discovery` | Direct classification without inference |

Full rlog is mandatory for CAN startup characterization. Qlog is sufficient for the newly added
error-level decision events, `CarParams`, and decimated panda health. A reboot can rotate or separate
boot evidence, so capture before rebooting whenever possible.

## Persistence across reboot

- `CarParams` and `CarParamsCache` clear on manager start. They do not make the decision persist
  across a full comma reboot.
- `CarParamsPersistent` and `CarParamsPrevRoute` persist. The former helps the XNOR flasher recognize
  that the previous car was a Rivian; neither is used as the fresh bus-1 fingerprint for `0x1310`.
- A fixed `CarPlatformBundle` persists and can force the platform, but it does not synthesize
  `0x1310` in the fresh fingerprint.
- Panda/external-module firmware and vehicle ECU/gateway state survive a process restart. Vehicle or
  kit state may also survive a comma reboot while the Rivian stays awake.

Thus, identical failure after a comma reboot followed by recovery only after Rivian sleep is strong
evidence for persistent vehicle/kit/CAN-side state, unless both failed boots independently show SPI
or USB transport faults.

## Route comparison

Run the analyzer separately for the four captures so each reboot has an independent monotonic epoch:

```bash
tools/rivian_dashcam_diagnostics.py bad-initial/*/rlog.zst --json bad-initial.json
tools/rivian_dashcam_diagnostics.py bad-reboot/*/rlog.zst --json bad-reboot.json
tools/rivian_dashcam_diagnostics.py recovered/*/rlog.zst --json recovered.json
tools/rivian_dashcam_diagnostics.py known-good/*/rlog.zst --json known-good.json
```

Interpret the comparison in this order:

1. No panda/discovery or broad SPI failures: processor/internal-panda transport.
2. Healthy panda but broad CAN silence or bus errors: harness, CAN, gateway, or ECU state.
3. Normal buses 0/2 but missing bus 1 or its kit IDs: Extreme Dev Kit path/routing/state.
4. `0x1310` present yet Rivian event says dashcam-only: software inconsistency requiring replay.
5. Rivian active but final passive reason differs: toggle/controller policy, not kit detection.

## History findings

The current flattened file attributes the gate to August 11 commit `0fd2acca2`, but equivalent
squashed/rebased angle-control commits contain the same gate back to at least May 11 (`0dd70241b`).
Repeated commit dates are not evidence that the gate is a recent regression.

Ranked hypotheses pending a bad route:

1. Extreme Dev Kit, its CAN routing, or Rivian ECU/gateway state fails to emit/deliver `0x1310` during
   the fingerprint window. Persistence until vehicle sleep fits this class best.
2. A startup timing issue allows Rivian identification before the kit begins emitting `0x1310`.
   The decision is boot-sticky and has no late recovery.
3. Processor/internal-panda SPI disruption loses enough startup CAN to omit `0x1310`. This should
   usually leave broader gaps, errors, or overflow evidence.
4. External USB discovery/setup failure affects XNOR module initialization. This requires correlated
   USB/pandad evidence; USB absence alone is not proof because native CAN uses SPI.
5. Generic passive causes (unrecognized car, missing controller, toggle off), distinguishable from
   the explicit events and `CarParams`.

## Next-occurrence checklist

Before rebooting or allowing the Rivian to sleep:

1. Leave the comma powered and run `tools/rivian_dashcam_collect.sh` from a computer on its network.
   It uses `$HOME/.ssh/config` by default; set `COMMA_SSH_CONFIG` when a different client config is required.
2. Label the output `bad-initial`; record the wall-clock time and whether the UI says dashcam mode.
3. Confirm `manifest.txt`, `system-state.txt`, Params, and recent rlog/qlog files exist.
4. Only then reboot the comma while keeping the vehicle awake and collect `bad-reboot`.
5. After natural Rivian deep sleep and the first successful boot, collect `recovered`.
6. Collect one ordinary startup as `known-good` and analyze all four states.

Do not reset vehicle modules, flash firmware, disconnect cables, or clear Params during this sequence.
Those actions erase or alter the state the comparison is intended to identify.

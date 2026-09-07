# Codex Task: Diagnose Intermittent Dashcam Mode on XNOR / Sunnypilot Rivian Builds

## Context

This workspace contains the exact XNOR build currently running on a comma four.

XNOR is a **Sunnypilot fork**, not a direct upstream openpilot build. Treat the code in this workspace as authoritative. Use upstream openpilot or Sunnypilot only as comparative references when useful, and do not assume their current behavior matches this fork.

The issue occurs intermittently on **two different Rivians**, each using an **XNOR Extreme Dev Kit** and a comma four.

Observed behavior:

- The system occasionally boots or transitions into **dashcam mode** instead of normal assisted-driving operation.
- The failure is infrequent.
- Once dashcam mode occurs, rebooting or power-cycling the comma four does **not** reliably recover normal operation.
- A normal Rivian soft reset also does not necessarily clear it.
- After the vehicle reaches a sufficiently deep sleep state, normal operation usually returns.
- The issue may have started around the time Janka mounts were installed in both vehicles.
- Because that change affected cable/device geometry, a marginal USB-C/device-side connection is one hypothesis.
- A recent XNOR/Sunnypilot software regression is another hypothesis.
- Long-duration recabling experiments are undesirable because the fault is rare.

The objective is to determine what telemetry already exists, identify the exact software path that selects dashcam mode, and add minimal instrumentation so the next occurrence can establish root cause.

---

## Primary Questions

### 1. What exact condition causes this build to enter dashcam mode?

Trace the complete code path from startup through the final decision that causes the system/UI to operate in dashcam-only/passive mode.

Do not stop at a generic `dashcamOnly` field.

Identify:

- where the relevant state originates;
- every condition that can cause it to become true;
- whether it is derived from vehicle identification, fingerprinting, interface configuration, safety initialization, a XNOR-specific condition, Sunnypilot behavior, or some other path;
- whether it can become sticky within a boot;
- whether any persisted state survives a comma reboot;
- what log evidence would identify the precise reason for entering dashcam mode.

Provide file paths, functions, classes, important conditions, and a concise call/data-flow explanation.

---

## 2. Trace Rivian Identification and Initialization

Trace the Rivian initialization path in this exact fork, including:

- panda/device discovery;
- USB enumeration;
- CAN receive startup;
- CAN bus assignment/mapping;
- fingerprinting or alternate vehicle-identification mechanisms;
- `CarParams` construction;
- Rivian interface selection;
- safety model and safety parameter initialization;
- XNOR Extreme Dev Kit-specific detection or configuration;
- any Sunnypilot-specific startup logic that differs from upstream openpilot;
- any retry, timeout, fallback, or passive-mode paths.

Determine which failures could plausibly produce this symptom:

> Supported Rivian enters dashcam mode, remains there across comma reboots while the Rivian stays awake, then recovers after the Rivian enters deep sleep.

Pay special attention to vehicle-side state that might persist while the Rivian remains awake.

---

## 3. Analyze USB Transport Health

Investigate the complete USB transport path between the comma four and any panda/XNOR hardware used by this build.

Identify:

- libusb usage;
- USB open/close logic;
- reconnect behavior;
- device reset behavior;
- endpoint/bulk-transfer code;
- receive/transmit error handling;
- retries;
- timeout handling;
- device disappearance/re-enumeration handling;
- kernel-visible USB events;
- whether `pandad` or any XNOR replacement/wrapper is used;
- whether multiple USB-connected devices are involved with the Extreme Dev Kit.

For every USB failure path, determine:

- whether it is logged;
- where it is logged;
- whether the original libusb/kernel error code is preserved;
- whether the software retries silently;
- whether counters already exist;
- whether errors appear in rlog/qlog, journald, Android/Linux logs, or another persistent location.

Search specifically for handling of conditions analogous to:

- `LIBUSB_ERROR_IO`
- `LIBUSB_ERROR_TIMEOUT`
- `LIBUSB_ERROR_NO_DEVICE`
- `LIBUSB_ERROR_PIPE`
- `LIBUSB_ERROR_OVERFLOW`
- enumeration failure
- device reset
- disconnect/reconnect
- endpoint stall

Also search kernel/system logging paths for events such as:

- `usb`
- `xhci`
- `reset`
- `disconnect`
- `reconnect`
- `device descriptor`
- `error -71`
- `error -110`
- `error -32`
- `unable to enumerate`

Do not assume these exact strings exist; find the equivalent paths for the platform in this workspace.

---

## 4. Determine Whether BER or Equivalent PHY/Error Statistics Exist

The user is particularly interested in whether a marginal physical USB-C connection can be detected quantitatively.

Determine whether any layer exposes:

- USB BER;
- PHY error counts;
- CRC failure counts;
- retry counts;
- link error counters;
- negotiated USB speed;
- link-state transitions;
- USB controller error counters;
- endpoint retry/error statistics;
- disconnect or reset counters;
- signal-quality diagnostics;
- Type-C/CC orientation or state information;
- power-delivery negotiation faults.

Check:

1. application/libusb layer;
2. kernel USB subsystem;
3. USB host controller / xHCI diagnostics;
4. sysfs/debugfs;
5. device firmware;
6. panda firmware;
7. comma four hardware/platform-specific interfaces.

If literal BER is unavailable, explicitly state that and identify the best available **USB link/transport health proxies**.

Prioritize diagnostics that can run continuously with negligible overhead.

---

## 5. Analyze Panda and CAN Health Telemetry

Identify all existing telemetry related to panda and CAN health.

Inspect messages such as, or equivalents to:

- `pandaStates`
- `peripheralState`
- `deviceState`
- `carParams`
- `carState`
- `can`
- manager/process state
- hardware state
- XNOR-specific cereal messages
- Sunnypilot-specific diagnostics

For `pandaStates` or equivalent, identify useful fields such as:

- panda count;
- panda type;
- serial number;
- firmware version/signature;
- ignition line;
- ignition CAN;
- harness status;
- safety model;
- safety parameter;
- faults;
- CAN receive/transmit error counters;
- heartbeat status;
- board health;
- uptime;
- bus state.

Determine which fields are already persisted in rlog/qlog and which are not.

---

## 6. Distinguish USB Failure from CAN/Vehicle-Side Failure

Design a diagnostic method that can distinguish these failure classes:

### A. USB/panda enumeration failure

Examples:

- panda absent;
- panda disappears/reappears;
- libusb errors;
- kernel reset/re-enumeration;
- wrong negotiated USB speed.

### B. Panda present, but CAN traffic absent or degraded

Examples:

- zero or near-zero frames;
- one expected bus missing;
- large receive gaps;
- abnormal CAN error counters;
- bus-off/recovery behavior.

### C. CAN traffic appears normal, but Rivian identification fails

Examples:

- expected IDs present;
- fingerprint mismatch;
- timeout before enough IDs arrive;
- bus mapping changed;
- unexpected ECU population.

### D. Rivian identifies correctly, but software intentionally selects dashcam/passive mode

Examples:

- valid `CarParams`;
- valid Rivian platform;
- explicit fork-specific flag;
- safety/configuration fallback;
- XNOR feature gate;
- Sunnypilot passive-mode logic.

For each class, state the minimum telemetry required to prove or strongly support it.

---

## 7. CAN Startup Characterization

For the first 30-60 seconds after ignition/startup, determine how to collect or compute, per CAN bus:

- frames per second;
- unique CAN addresses;
- first frame timestamp;
- last frame timestamp;
- longest receive gap;
- total frame count;
- changing vs static IDs;
- expected Rivian-critical IDs if known from this codebase;
- CAN error state;
- bus-off events;
- recovery events.

The goal is to compare a good startup against a dashcam-mode startup.

If the necessary data already exists in rlog, provide a script or exact analysis approach for extracting it.

---

## 8. Compare Four Diagnostic States

Design the analysis around these four states:

1. **Normal boot**
2. **Initial dashcam-mode failure**
3. **Comma reboot while Rivian remains awake and dashcam mode persists**
4. **First successful boot after Rivian deep sleep**

For each state, compare:

### USB

- device presence;
- topology/path;
- VID/PID;
- serial;
- negotiated speed;
- open count;
- reconnect/reset count;
- transfer errors;
- kernel USB messages.

### Panda

- number of devices;
- serials;
- firmware;
- faults;
- ignition state;
- safety configuration;
- harness state.

### CAN

- frames/sec by bus;
- unique IDs by bus;
- missing buses;
- receive gaps;
- error counters;
- bus-off state.

### Vehicle identification

- candidate vehicles;
- fingerprint source;
- fingerprint result;
- firmware matching if applicable;
- Rivian platform selected;
- relevant `CarParams`.

### Dashcam decision

- exact boolean/enum/state;
- source;
- reason;
- timestamp;
- code path.

The most important discriminator is:

> Does the failed comma reboot have fully healthy USB/panda communication but a different Rivian CAN/ECU population that only returns to normal after vehicle sleep?

If yes, that strongly shifts suspicion away from the mount/USB physical layer and toward vehicle-side ECU/gateway state.

---

## 9. Existing Logs: What Can Be Learned Without Modifying the Build?

Before proposing code changes, determine exactly what can already be recovered from a route exhibiting the fault.

Document:

- which route files are needed;
- whether full `rlog` is required or `qlog` is sufficient;
- whether boot logs exist outside route logs;
- whether journald/kernel logs are captured;
- retention limitations;
- whether a comma reboot loses important pre-reboot evidence;
- how to export/copy the necessary files before vehicle sleep or further resets.

Provide commands or scripts where appropriate.

---

## 10. Propose a Minimal Diagnostic Patch

After identifying existing telemetry gaps, implement or propose a **minimal, low-overhead diagnostic patch**.

Prefer existing logging/cereal infrastructure rather than creating a large subsystem.

At minimum, consider persistent counters/state for:

```text
usb_open_count
usb_disconnect_count
usb_reconnect_count
usb_reset_count
usb_rx_error_count
usb_tx_error_count
usb_timeout_count
usb_io_error_count
usb_pipe_error_count
usb_no_device_count
last_usb_error
last_usb_error_mono_time
panda_reconnect_count
```

At device/panda initialization, capture if available:

```text
USB VID
USB PID
USB bus
USB device path/topology
negotiated USB speed
USB serial
panda serial
panda type
panda firmware version
panda firmware signature
```

Also log an explicit **dashcam-mode reason** rather than just a boolean.

Example conceptually:

```text
dashcam_mode = true
dashcam_reason = "RIVIAN_FINGERPRINT_TIMEOUT"
```

Possible reason categories might include:

```text
NO_PANDA
USB_DEVICE_LOST
NO_CAN_TRAFFIC
MISSING_REQUIRED_CAN_BUS
UNKNOWN_VEHICLE
FINGERPRINT_TIMEOUT
FIRMWARE_MATCH_FAILED
UNSUPPORTED_CARPARAMS
SAFETY_INIT_FAILED
XNOR_CONFIG_FALLBACK
SUNNYPILOT_PASSIVE_MODE
UNKNOWN
```

Do not invent these as actual production enums unless justified by the code. Derive the real categories from the implementation.

The patch should have negligible performance and storage impact.

---

## 11. Consider a Startup Diagnostic Snapshot

Evaluate whether it would be useful to emit a single structured diagnostic snapshot roughly 10-30 seconds after startup containing:

- detected USB devices;
- USB speeds;
- panda identities;
- panda faults;
- CAN frame counts by bus;
- CAN unique IDs by bus;
- fingerprint result;
- selected vehicle;
- safety configuration;
- dashcam/passive state;
- dashcam reason.

If useful, implement this using existing cereal/logging mechanisms.

---

## 12. Investigate Stickiness Across Comma Reboots

A critical observation is that the failure can remain after rebooting the comma while the Rivian remains awake.

Investigate whether any XNOR/Sunnypilot behavior could cause persistence through:

- files on disk;
- Params;
- cached fingerprints;
- cached `CarParams`;
- persistent configuration;
- previous-route state;
- panda firmware state;
- Extreme Dev Kit state;
- USB device firmware state.

Separate these from **vehicle-side persistence**, where the comma starts cleanly but receives a different network state because one or more Rivian ECUs have not reset.

Explicitly state which kinds of state survive a comma reboot in this build.

---

## 13. Review Recent Relevant Changes

Inspect recent git history in this workspace and identify changes affecting:

- Rivian;
- fingerprinting;
- car identification;
- panda;
- USB;
- `pandad`;
- CAN;
- safety;
- ignition detection;
- startup sequencing;
- dashcam/passive mode;
- XNOR hardware;
- Extreme Dev Kit support;
- Sunnypilot-specific car interface logic.

Look especially for changes around the approximate recent update window rather than assuming current HEAD has always behaved this way.

For suspicious changes, explain the plausible failure mechanism.

Do not modify or revert code solely based on correlation.

---

## 14. Deliverables

Produce the following:

### A. Root-cause map

A concise flow diagram or structured explanation:

```text
USB enumeration
    ->
panda available
    ->
CAN buses alive
    ->
Rivian identification
    ->
CarParams
    ->
safety/configuration
    ->
normal operation OR dashcam mode
```

Annotate every point where this fork can fall into dashcam mode.

### B. Existing telemetry inventory

A table with:

| Signal | Already logged? | Location/message | Useful for this fault? |
|---|---|---|---|

### C. USB diagnostic assessment

State clearly:

- whether literal BER is available;
- what equivalent link-health counters exist;
- what is already logged;
- what needs instrumentation.

### D. Good-vs-bad route comparison procedure

Provide commands/scripts for comparing:

- normal boot;
- failure;
- persistent failure after comma reboot;
- recovery after Rivian sleep.

### E. Minimal diagnostic patch

Implement it if practical.

Keep changes isolated and easy to revert.

### F. Suspect code/history findings

List any code paths or recent commits that plausibly explain the symptom, ranked by confidence.

### G. Next-occurrence collection checklist

Provide an operator checklist requiring minimal intervention.

It should prioritize capturing evidence **before rebooting or allowing the Rivian to sleep**.

---

## Constraints

- This is an intermittent fault. Do not require intentionally reproducing it.
- Avoid recommendations that require driving for weeks with awkward recabling.
- Instrumentation must have negligible runtime impact.
- Preserve existing XNOR/Sunnypilot behavior except where diagnostic logging is added.
- Do not assume upstream openpilot behavior applies to this fork.
- Prefer evidence from the code and logs in this workspace over generic documentation.
- Do not perform destructive vehicle resets as part of analysis.
- Do not flash firmware merely for diagnostic purposes.
- Treat physical USB-C/mount strain as a hypothesis, not a conclusion.
- Treat Rivian ECU/gateway state persisting until deep sleep as a major competing hypothesis.

---

## Suggested Interpretation Matrix

Use this as a starting framework, but adapt it to the actual implementation:

| Observation during bad boot | Likely direction |
|---|---|
| USB device absent | connector, cable, power, enumeration |
| USB resets/errors immediately before failure | physical/link layer or USB stack |
| USB healthy, panda absent | panda/XNOR device initialization |
| Panda healthy, all CAN buses nearly silent | harness, vehicle network, ECU state |
| One expected CAN bus missing | harness/interface/gateway state |
| CAN traffic normal, Rivian unidentified | fingerprint/identification regression |
| Rivian correctly identified, dashcam flag true | XNOR/Sunnypilot policy/config/safety path |
| Comma reboot identical failure, vehicle sleep fixes | persistent vehicle-side ECU/gateway state becomes highly suspect |
| Failure follows specific comma/cable across vehicles | device-side hardware/USB becomes more suspect |

---

## Desired Outcome

The next time this rare event occurs, existing or newly added logs should be sufficient to answer:

> Did the comma lose or degrade its USB connection to the XNOR/panda hardware, did CAN connectivity change, did Rivian identification fail despite healthy transport, or did XNOR/Sunnypilot intentionally choose dashcam mode after otherwise successful initialization?

The analysis should narrow the fault to one of those layers without requiring prolonged hardware swapping.

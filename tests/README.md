# B-AACC Wire Tests

Tests that drive the running example over BACnet/IP from outside it. B-AACC is a
**Blocked Example** (stack #2150, #2044): its Profile Function, authentication
and authorization for physical access, cannot be performed through the stack's
customer interface, so there is nothing to test for it yet, and the A-side
sends (to a B-ACDC peer) are not tested here. What is tested is
what a client discovering the device sees: every property every object lists
must read as a value. They are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this example is here. Python 3 standard library only - nothing to
`pip install`.

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBAACC
```

On Windows, `--exe build\Release\BACnetExampleBAACC.exe`. It ends with
`ALL WIRE TESTS PASSED` (exit 0) or the scripts that failed. `--port` (default
47830) is the UDP port the test starts the device on. It takes about ten
seconds. CI (`.github/workflows/release.yml`) runs it on Linux after the smoke
test.

## The setup

```
test client (127.0.0.1, ephemeral UDP port)  - the Peer
    |  BACnet/IP, unicast
BACnetExampleBAACC  UDP --port                - Device 389010
```

The Peer is a Python BACnet client (`wiretest.Client`), never another example's
binary. It plays a BACnet client such as Chipkin BACnet Explorer.

## `discovery_test.py` - every listed property reads as a value

Copied from B-SS-CPP (`da3e96f`). The device instance, executable name, port
and the expected-object control list are this example's; two additions are
explained below.

1. **Who-Is** (for 389010, unicast) -> the device's I-Am.
2. **Device `Object_List`** names exactly the 17 objects `main.cpp` creates:
   the Device, the three sensors, Access Door 1, Credential Data Input 1,
   Access Point 1, Access Zone 1, Access Credential 1, Access Rights 1, Access
   User 1, Event Log 1, Schedule 1, Calendar 1, File 1, Notification Class 1 and Network Port
   1. This is the control: a walk over nothing would pass.
3. For each object, **`Property_List`** reads, and a ReadProperty of every
   property it lists - plus `Object_Identifier`, `Object_Name`, `Object_Type`
   and `Property_List`, which cl. 12.1.1.4.1 leaves out of the list - returns a
   ComplexACK. An Error, Reject, Abort or no answer prints an `[UNREADABLE]` line
   and fails the check. 135-2024 cl. 12.1.1.4.1: Property_List holds "one
   property identifier for each property that exists within the object".
4. Network Port 1's **`IP_DNS_Server` (406)**, **`FD_BBMD_Address` (418)** and
   **`FD_Subscription_Lifetime` (419)** are each listed and read as a value -
   the three reads Chipkin BACnet Explorer found failing at stack 6.0.21
   (reported against B-SS-CPP as #20, #21, #22).
5. **Access Door 1 pulse**: Present_Value PULSE_UNLOCK at priority 8 gets a
   SimpleACK; during the pulse Present_Value reads PULSE_UNLOCK and Lock_Status
   unlocked; after Door_Pulse_Time (3.0 s) Present_Value reads LOCK again
   (135-2024 cl. 12.26.4, 12.26.16).

Additions to the B-SS test:

- **DS-COV-B on Analog Input 1:** it lists `COV_Increment` (22) in its
  `Property_List` and it reads 1.0 (required where an Analog Input supports COV
  reporting, cl. 12.2 footnote 2); a SubscribeCOV with an 8-hour lifetime
  (28800 s) is SimpleACKed (the BTL Test Plan requires 8-hour lifetimes for
  DS-COV-B, 135.1 9.10.1.10), one with 28801 s is refused with an Error, and the
  cancellation is SimpleACKed.
- **Event Log 1 `Log_Buffer` (131) must answer Error property /
  read-access-denied**, and is its own check. The standard makes it
  ReadRange-only: "The log buffer is not network accessible except through the
  use of the ReadRange service" (cl. 12.27.13), and cl. 15.5.1.3.1 answers "The
  property is not accessible using this service" with PROPERTY /
  READ_ACCESS_DENIED. A value would fail it too.
- **Five properties are `[KNOWN GAP]`s** (stack #2150, TODO.md #2): Access
  Credential `Assigned_Access_Rights` and `Authentication_Factors`, Access
  Point `Access_Doors`, Access Rights `Negative_Access_Rules` and
  `Positive_Access_Rules`. (Access Point `Access_Event_Credential` was a sixth
  until Stack Pin `69b6249f`, where it reads as a value; it is now checked like
  every other property.) Each is read and
  reported on every run without failing it; when one reads as a value the run
  prints `[GAP CLOSED]`. (Access User 1 `Credentials` reads as an empty list, so
  it passes; TODO.md #2 says why that is still a gap.)

## `recipient_list_test.py` - Notification Class 1's Recipient_List is writable

1. The default list (the entry `main.cpp` seeds) reads back as one
   BACnetDestination.
2. A WriteProperty of a two-entry list (Device 389110, Process Identifier 2,
   confirmed; Device 389111, Process Identifier 3, unconfirmed, to-offnormal
   only) is SimpleACKed and reads back unchanged.
3. Writing the default back is SimpleACKed and reads back unchanged.

On a binary where the list is read-only, both writes answer Error PROPERTY /
WRITE_ACCESS_DENIED (2/5). Delivery is not tested: this example generates no
event notification (TODO.md #1).

## `time_sync_test.py` - a workstation sets the device clock (DM-TS-B, DM-UTC-B)

1. Control: before any sync, Local_Date is the host's date.
2. TimeSynchronization 2026-12-25 10:00 -> Local_Date reads 2026-12-25 and
   Local_Time about 10:00.
3. UTCTimeSynchronization Monday 2026-10-19 07:00 (UTC_Offset 0) -> Local_Date
   2026-10-19, Local_Time about 07:00.

Before the fix the device acknowledged both requests but Local_Date / Local_Time
kept reporting the host clock.

## It fails without the fix

The example's own three defects this test found were fixed in `main.cpp` in
the same change. With the same stack (`64b2cfac5`) and the previous `main.cpp`
the run failed with 11 unreadable reads (Windows STATIC):

```
[UNREADABLE] Device 389010 property 56: Error class=2 code=27
[UNREADABLE] Device 389010 property 57: Error class=2 code=27
[UNREADABLE] Schedule 1 property 85: Error class=2 code=72
[UNREADABLE] Event Log 1 property 131: Error class=2 code=27
[UNREADABLE] Access Credential 1 property 256: Error class=2 code=32
[UNREADABLE] Access Credential 1 property 257: Error class=2 code=32
[UNREADABLE] Access Point 1 property 246: Error class=2 code=32
[UNREADABLE] Access Point 1 property 249: Abort reason=0
[UNREADABLE] Access Rights 1 property 288: Error class=2 code=32
[UNREADABLE] Access Rights 1 property 302: Error class=2 code=32
[UNREADABLE] Credential Data Input 1 property 304: Error class=2 code=32
```

- Device `Local_Date` (56) / `Local_Time` (57), read-access-denied: listed
  because the device executes TimeSynchronization and UTCTimeSynchronization
  (Table 12-13 footnotes 3 and 4), but the example's Date/Time callbacks never
  answered them. Fixed: they answer wall-clock local time.
- Schedule 1 `Present_Value` (85), value-not-initialized: the stack's Schedule
  engine evaluates from the Device's `Local_Date` / `Local_Time`, so it had
  never run. Fixed by the same change; Saffron now writes Cobalt in its window.
- Credential Data Input 1 `Supported_Formats` (304), unknown-property: the
  example never served the array's length (index 0). Fixed: it does, as
  B-ACCR does.

The remaining eight are `Log_Buffer` (correct, see above) and the six #2150
gaps (five at Stack Pin `69b6249f`).

## Results

Run 2026-10-15, stack `6.x` @ `64b2cfac5` (6.0.23), the committed `main.cpp`:

| Platform | Build | Result |
|---|---|---|
| Windows | STATIC (msbuild `ReleaseLib|x64`, VS 18) | 24/24 - PASS, 249 reads, 6 known gaps |
| Linux (WSL Ubuntu 22.04) | STATIC (`projects/linux` makefile) | 24/24 - PASS, 249 reads, 6 known gaps |

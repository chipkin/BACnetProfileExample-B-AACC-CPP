# BACnet B-AACC (Advanced Access Control Controller) - C++ example

> **Blocked Example.** The CAS BACnet Stack cannot yet perform the B-AACC
> Profile Function - authentication and authorization for physical access,
> configured through the device's Access User, Access Credential and Access
> Rights objects, using remote door controllers and credential readers, and
> reported as access events (ANSI/ASHRAE 135-2024 Annex L.6.1) - through its
> customer interface, so this example stays published but is **blocked** on
> two stack gaps. On 2026-10-15 the stack owner ruled that neither is promoted
> to the customer interface for now:
>
> - **[cas-bacnet-stack#2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150)** -
>   the properties that carry the authorization data cannot be served: an
>   Access Credential's `Authentication_Factors` and `Assigned_Access_Rights`,
>   an Access Rights object's `Positive_Access_Rules` and
>   `Negative_Access_Rules`, an Access Point's `Access_Doors` (each answers
>   Error unknown-property) and `Access_Event_Credential` (Abort). So another
>   device cannot read or configure who may pass where, and DS-ACUC-B and
>   DS-ACSC-B cannot be claimed.
> - **[cas-bacnet-stack#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044)** -
>   no customer-facing algorithm generates an ACCESS_EVENT notification, so
>   AE-AC-B (and with it AE-EL-I-B) cannot be claimed.
>
> What it does today: everything B-ACC-CPP does (a discoverable BACnet/IP
> device with the access object family, a Schedule that unlocks its door,
> COV, DeviceCommunicationControl, time synchronization, ReinitializeDevice,
> backup/restore), plus an Access User object, and it **sends** ReadProperty,
> WriteProperty and SubscribeCOV to a peer's door. It cannot use the replies
> (no customer callback delivers them), and it makes **no** grant/deny
> decision.

A minimal, copy-paste-friendly example showing how to implement the BACnet
**B-AACC (Advanced Access Control Controller)** device profile in C++ using
the [CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack).
It serves the access-control object family over **BACnet/IP (UDP 47808)**,
and it also **initiates** requests of its own (ReadProperty, WriteProperty,
SubscribeCOV) against a peer device. Seeded from **B-ACC-CPP** (Access
Control Controller) and extended, not rebuilt: this repository serves
everything B-ACC-CPP serves, plus an Access User object and the A-side
(client) keys described below.

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to
  review it for conformance. Read it when you start turning this into your
  own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.

> **Versions:** this document describes **example v1.1.0**, built and verified
> against **CAS BACnet Stack 6.0.23** (`6.x` @ `64b2cfac5`), at
> **Protocol_Revision 30**, with the vendored `common/` helper at **v3.3.0**.
> Running the example prints all three - if what it prints disagrees with this
> line, trust the program and check `CHANGELOG.md`.

## What is the B-AACC (Advanced Access Control Controller) profile?

**B-AACC**, defined in Annex L.6.1 of ANSI/ASHRAE 135-2024, "performs
physical access control authentication and authorization for physical access.
It supports the modification of its Access User, Access Credential, and Access
Rights objects by another device. ... It is capable to use remote Access
Control Door Controller devices and remote Access Control Credential Reader
devices." Compared with B-ACC (L.6.2) it adds Access User objects, the A-side
(it reads, writes and subscribes to other devices as a client - a head-end
access controller talking to subordinate door controllers), event logging and
backup/restore. This example does not perform that function (see the Blocked
Example note above).

## The device this example creates

| Object | Name | Notes |
|---|---|---|
| Device 389010 | Chipkin Example B-AACC | `--deviceID` overrides |
| Analog Input 1 | Bronze | REAL, degrees Celsius; read-only; COV-subscribable |
| Binary Input 1 | Emerald | active/inactive; read-only |
| Multi-State Input 1 | Hot Pink | state 1..3; read-only |
| Access Door 1 | Cobalt | BACnetDoorValue; commandable (lock/unlock); SCHED-I-B target |
| Credential Data Input 1 | Flax | AuthenticationFactor; Update_Time COV-subscribable |
| Access Point 1 | Copper | Access_Event writable (demo); Authorization_Mode writable, stored, gates nothing |
| Access Zone 1 | Ebony | Occupancy_State |
| Access Credential 1 | Coral | Credential_Status |
| Access Rights 1 | Cyan | Enable; Global_Identifier writable |
| **Access User 1** | **Denim** | **New in this profile.** User_Type; Global_Identifier writable; Credentials an empty list (TODO.md #2) |
| Event Log 1 | Beige | logs nothing: no event notification is ever generated (TODO.md #1) |
| Schedule 1 | Saffron | writes Cobalt at priority 12 |
| Calendar 1 | Cream | Date_List empty: added with the generic `AddObject`, not the stack's Calendar engine (TODO.md #3) |
| File 1 | Ivory | stream access, backup/restore payload |
| Notification Class 1 | Crimson | routes Copper's alarms |
| Network Port 1 | Vermilion | BACnet/IP |

## What this example supports

The example implements as much of the B-AACC profile as the CAS BACnet
Stack's customer-facing API supports today. `docs/PICS.md` lists every BIBB,
every service, every object and every property, with a ✅/☐ for each - the
table below is the summary.

### BIBBs (BACnet Interoperability Building Blocks)

| BIBB | Description | Supported |
|------|-------------|:---------:|
| DS-RP-B, DS-RPM-B | ReadProperty / ReadPropertyMultiple (execute) | ✅ |
| DS-RP-A | ReadProperty (**initiate** - `SendReadProperty`, key 'd') | ☐ partial: the request is sent; the reply cannot be consumed (no customer callback, TODO.md #6) |
| DS-WP-B, DS-WPM-B | WriteProperty / WritePropertyMultiple (execute) | ✅ |
| DS-WP-A | WriteProperty (**initiate** - `SendWriteProperty`, key 'w') | ✅ sends (changed a B-ACDC peer's door at v1.0.0; the result cannot be observed in-process, TODO.md #6) |
| DS-COV-B | SubscribeCOV (execute - Bronze's Present_Value, Flax's Update_Time) | ✅ |
| DS-COV-A | SubscribeCOV (**initiate** - `SendSubscribeCOV`, key 'r') | ☐ the request is sent, but has never succeeded (the B-ACDC peer has no SubscribeCOV) and notifications cannot be received (TODO.md #6) |
| DS-ACAD-A | Data Sharing - Access Control Access Door - A (K.1.37: read and write all forms of all standard properties of Access Door objects) | ☐ not claimed: only the peer door's `Present_Value` is touched |
| DS-ACCDI-A | Data Sharing - Access Control Credential Data Input - A (K.1.39) | ☐ not claimed (TODO.md #5) |
| DS-ACUC-B | Data Sharing - Access Control User Configuration - B (K.1.34: read/write the standard properties of Access Rights, Access User, Access Credential) | ❌ blocked on [#2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150) |
| DS-ACSC-B | Data Sharing - Access Control Site Configuration - B (K.1.36: read/write the standard properties of Access Point, Access Zone, Access Door, Credential Data Input) | ❌ blocked on [#2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150) (Access Point) |
| AE-AC-B | Alarm and Event Management - Access Control - B (K.2.32: generate ACCESS_EVENT notifications) | ❌ blocked on [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) |
| AE-ACK-B, AE-INFO-B | Accept AcknowledgeAlarm, answer GetEventInformation | ✅ |
| AE-EL-I-B | Alarm and Event Management - Event Log - Internal - B (K.2.21: collect event notifications in an internal buffer) | ❌ nothing to collect: no notification is generated (#2044) |
| SCHED-I-B | Schedule/Calendar initiate (Saffron unlocks Cobalt on a schedule) | ✅ |
| DM-BR-B | Backup and Restore (Ivory carries the payload) | ✅ |
| DM-DDB-A,B, DM-DOB-B | Who-Is/I-Am (answer + initiate), Who-Has/I-Have | ✅ |
| DM-DCC-B | DeviceCommunicationControl | ✅ |
| DM-TS-B / DM-UTC-B | TimeSynchronization / UTCTimeSynchronization | ✅ |
| DM-RD-B | ReinitializeDevice (also drives the backup/restore state machine) | ✅ |

**DS-ACCDI-A is not claimed.** It needs a COV subscription to a remote
Credential Data Input and the ability to receive the AuthenticationFactor
values in the notifications; this example sends no such subscription and has
no customer callback to receive notifications. See `TODO.md` #5 and #6.

**AE-AC-B is not claimed.** No intrinsic algorithm on the customer-facing
surface can generate an `accessEvent`-typed notification at this pin, and the
stack rejects the generic change-of-state algorithm on an Access Point, so no
notification of any kind is produced. Access Point 1 ("Copper")'s
`Access_Event` property is real and writable. (Earlier versions of this
README said a `changeOfState` notification was produced instead; it was not.)
See `TODO.md` #1.

**DS-ACUC-B and DS-ACSC-B are not claimed.** Earlier versions named them
"Unlock Command" and "Supervisory Command" and ticked them for the door and
Authorization_Mode writes. K.1.34 and K.1.36 define them as answering reads
and writes of the standard properties of the access objects, which stack
#2150 prevents. See `TODO.md` #2.

### Services and objects

`docs/PICS.md` section 4 lists every service this device both **executes**
(server / B-side) and **initiates** (client / A-side) - this profile does
both. Section 6 lists every object type and instance this device creates.

## A-side (client) keys

New in this profile, on top of everything B-ACC-CPP serves. This device also
**initiates** requests against a peer device - a separately-built,
separately-run local instance of
[BACnetProfileExample-B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP)
(device 389011 "Chipkin Example B-ACDC", Access Door 1 "Cobalt"), not modified by this
repository:

| Key | Service | Target |
|---|---|---|
| `d` | `SendReadProperty` (DS-RP-A) | peer's Access Door 1 (Cobalt) `Present_Value` |
| `w` | `SendWriteProperty` (DS-WP-A) | peer's Access Door 1 (Cobalt) `Present_Value` (toggles lock/unlock, priority 8) |
| `r` | `SendSubscribeCOV` (DS-COV-A) | peer's Access Door 1 (Cobalt), 300s lifetime, confirmed notifications |

All three also fire once automatically at start-up, so a scripted/headless
run (no interactive keyboard) still exercises the A-side without a human
pressing a key. The peer's IP/port default to `127.0.0.1:47809`; override
with `--peerIp <a.b.c.d>` / `--peerPort <n>`.

**A known limitation, not a functional break:** the CAS BACnet Stack's
customer-facing API has no callback to observe a received ReadProperty-Ack,
WriteProperty SimpleAck, or COV notification in-process, so this device's own
console can only confirm a `Send*` call was *accepted by the local stack for
transmission*, not that a reply arrived - the actual round trip is verified
independently on the wire (see [Verify](#verify) below, and `TUTORIAL.md`).

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial
Chipkin product** - it is not free or open source, and there is no
public/trial build. The stack is referenced here as the **private** git
submodule `submodules/cas-bacnet-stack`; you can only fetch and build it once
you have a CAS BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example, or to run a
[prebuilt release binary](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP/releases).
The licence is what lets you *build* it - that is the part the stack
submodule gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device.
- `tests/` - the Wire Tests (see [Wire Tests](#wire-tests)), and `wiretest/`, the
  series' shared Python harness they are written against (vendored, like `common/`).
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS.
- `docs/PICS.md` - the conformance statement.
- `docs/objects.json` - source for `docs/PICS.md`'s generated objects table.
- `TODO.md` - every known gap, verified against the pin and/or the wire, with
  filed stack issues.
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into
  the executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).

### Windows

- **C++ compiler** - install
  [Visual Studio Community](https://visualstudio.microsoft.com/downloads/)
  (free) and select the **"Desktop development with C++"** workload.
- **CMake** - from <https://cmake.org/download/>, or `winget install Kitware.CMake`.

### Linux / macOS

- Debian/Ubuntu: `sudo apt install build-essential cmake git`
- macOS: `xcode-select --install` and `brew install cmake`

## Build

CMake only, and the same two commands on every platform:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP.git
cd BACnetProfileExample-B-AACC-CPP

cmake -B build -S .
cmake --build build --config Release
```

Already cloned without `--recursive`? Run `git submodule update --init --recursive`
first - the build needs the stack submodule.

> **The first build takes a few minutes** - it compiles the entire CAS BACnet
> Stack (~600 source files) into the executable. Rebuilds after that are
> incremental and take seconds.

If your CAS BACnet Stack lives somewhere other than the bundled submodule,
point CMake at it: `cmake -B build -S . -D CAS_STACK_DIR=/path/to/cas-bacnet-stack`.

## Run

```bash
# Linux / macOS
./build/BACnetExampleBAACC

# Windows
.\build\Release\BACnetExampleBAACC.exe
```

Expected output:

```
BACnet Advanced Access Control Controller (B-AACC) Example - C++ v1.1.0
CAS BACnet Stack version: 6.0.23.0
Common helper (common/) version: 3.3.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
TX 21 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1) - Unconfirmed: I-Am
TX 8 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1) - Unconfirmed: Who-Is
FYI: Device 389010 ("Chipkin Example B-AACC") ready. Vendor ID 389. Press 'h' for help.
FYI: A-side peer target 127.0.0.1:47809 (override with --peerIp/--peerPort). Keys: 'd' SendReadProperty, 'w' SendWriteProperty, 'r' SendSubscribeCOV - all to the peer's Access Door 1.
TX 17 bytes to 127.0.0.1:47809 (Network Port 1) - ConfirmedRequest: ReadProperty Access_Door 1.Present_Value
A-side: sent SendReadProperty to peer 127.0.0.1:47809 (Access Door 1 Present_Value).
TX 23 bytes to 127.0.0.1:47809 (Network Port 1) - ConfirmedRequest: WriteProperty Access_Door 1.Present_Value
A-side: sent SendWriteProperty to peer (Access Door 1 Present_Value <- 1 [unlock]).
TX 22 bytes to 127.0.0.1:47809 (Network Port 1) - ConfirmedRequest: SubscribeCOV
A-side: sent SendSubscribeCOV to peer (Access Door 1, 300s lifetime).
```

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see below).

> **Red `Error:` lines at start-up are expected and are not your bug** - the
> stack's own debug logging shared by every example in this series (the device
> hearing its own broadcast I-Am, a one-time BACnet/SC UUID notice).
> [TUTORIAL.md](TUTORIAL.md#troubleshooting) explains it. (The continuous log
> flood an Event Log caused at stack 6.0.21,
> [#2045](https://github.com/chipkin/cas-bacnet-stack/issues/2045), is fixed at
> this pin.)

### Two-instance test setup (this device + its A-side peer)

```bash
# Terminal 1: the peer (B-ACDC-CPP, unmodified, its own default port)
cd BACnetProfileExample-B-ACDC-CPP
./build/BACnetExampleBACDC --port 47809

# Terminal 2: this device
cd BACnetProfileExample-B-AACC-CPP
./build/BACnetExampleBAACC --port 47808 --peerPort 47809
```

### Command-line options

| Option | Default | Meaning |
|--------|---------|---------|
| `--port <n>` | `47808` | UDP port to listen on (BACnet/IP). |
| `--deviceID <n>` | `389010` | The device's BACnet instance number (BACnet requires this to be configurable). |
| `--peerIp <a.b.c.d>` | `127.0.0.1` | The A-side peer's IP address. |
| `--peerPort <n>` | `47809` | The A-side peer's UDP port. |
| `--help`, `-h` | - | Show usage and exit. |
| `--version` | - | Print the example, stack, and `common/` helper versions, then exit. |

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1 (also feeds its COV subscribers). |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |
| `d` | `SendReadProperty` (DS-RP-A) to the peer's Access Door 1. |
| `w` | `SendWriteProperty` (DS-WP-A) to the peer's Access Door 1 (toggles lock/unlock). |
| `r` | `SendSubscribeCOV` (DS-COV-A) to the peer's Access Door 1. |

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer),
plus a real second local instance of B-ACDC-CPP as the A-side peer:

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389010** (vendor **389**). It also broadcasts an I-Am at
   start-up.
2. **Browse the object model** - the device shows seventeen objects (see
   [The device this example creates](#the-device-this-example-creates)).
   Reading the Device's `Object_List` returns all of them.
3. **Read the Device** - ReadProperty `389010` -> `Object_Name` returns
   `"Chipkin Example B-AACC"`; `Protocol_Revision` returns `30`.
4. **Door command** - WriteProperty Cobalt's `Present_Value` to `unlock`(1) at a
   priority; confirm `Lock_Status`/`Door_Status` follow; relinquish and
   confirm it falls back to `Relinquish_Default` (`lock`).
5. **Access User 1 (Denim)** - ReadProperty `Object_Name` returns `"Denim"`;
   WriteProperty `Global_Identifier` and read it back.
6. **A-side** - press `d`/`w`/`r` (or wait for the automatic start-up fire)
   and watch the **peer's own console** for the effect: `SendWriteProperty`
   genuinely changes the peer's door state. This device's own console only
   confirms local acceptance for transmission, not the peer's reply - see
   [A-side (client) keys](#a-side-client-keys).
7. **Confirm the documented gaps stay gaps** - `docs/PICS.md` and `TODO.md`
   list every property/service this build cannot serve; confirm a read of
   one of them (e.g. Access Credential's `Authentication_Factors`) fails the
   way TODO.md says it does, not silently.

For a property-by-property review against the conformance statement, and the
full Troubleshooting table, see [TUTORIAL.md](TUTORIAL.md).

## Wire Tests

A Python BACnet client drives the running example over BACnet/IP from outside
it, the way a client discovers a device - Who-Is, the Device's `Object_List`,
then for every object its `Property_List` and a ReadProperty of every property
it lists. Every read must come back as a value, except the Event Log's
`Log_Buffer`, which the standard makes ReadRange-only. The six properties stack
#2150 cannot serve are reported as `[KNOWN GAP]` lines and do not fail the run.
Python 3 standard library only:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBAACC          # Linux/macOS
python tests\run_wire_tests.py --exe build\Release\BACnetExampleBAACC.exe   # Windows
```

It ends with `ALL WIRE TESTS PASSED` (exit 0). CI runs it on Linux after the
smoke test. [tests/README.md](tests/README.md) says what each check proves. It
tests the B side only: it does not test the Profile Function (the example
cannot perform it) or the A-side sends.


## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
There is one example repository per standardized device profile in ASHRAE 135-2024 Annex L. An example marked ⛔ is blocked: the stack cannot yet perform that profile's function through its customer interface, and the example's README says what it does today. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

### Controllers (Annex L.4)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) | [B-SS-Node](https://github.com/chipkin/BACnetProfileExample-B-SS-Node) | [B-SS-CS](https://github.com/chipkin/BACnetProfileExample-B-SS-CS) | [B-SS-Rust](https://github.com/chipkin/BACnetProfileExample-B-SS-Rust) | [B-SS-Python](https://github.com/chipkin/BACnetProfileExample-B-SS-Python) | [B-SS-Go](https://github.com/chipkin/BACnetProfileExample-B-SS-Go) |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) | [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) | Ask | Ask | Ask | Ask |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Life safety controllers (Annex L.5)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 🚧 | Ask | Ask | Ask | Ask | Ask |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Access control controllers (Annex L.6)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |

### Lighting controllers (Annex L.11)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Elevator controllers (Annex L.13)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Authentication and authorization (Annex L.14)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) ⛔ blocked on [stack #2043](https://github.com/chipkin/cas-bacnet-stack/issues/2043) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ⛔ blocked on [stack #3934](https://github.com/chipkin/cas-bacnet-stack/issues/3934) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ⛔ blocked on [stack #2032](https://github.com/chipkin/cas-bacnet-stack/issues/2032) | Ask | Ask | Ask | Ask | Ask |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | — | — | — | — | — |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12)

Client-side profiles.

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-OWS** Operator Workstation | planned | — | — | — | — | — |
| **B-AWS** Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-XAWS** Extended Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-LSAP** Life Safety Annunciator Panel | planned | — | — | — | — | — |
| **B-LSWS** Life Safety Workstation | planned | — | — | — | — | — |
| **B-ALSWS** Advanced Life Safety Workstation | planned | — | — | — | — | — |
| **B-ACSD** Access Control Security Display | planned | — | — | — | — | — |
| **B-ACWS** Access Control Workstation | planned | — | — | — | — | — |
| **B-AACWS** Advanced Access Control Workstation | planned | — | — | — | — | — |
| **B-LOD** Lighting Operator Display | planned | — | — | — | — | — |
| **B-ALWS** Advanced Lighting Workstation | planned | — | — | — | — | — |
| **B-LCS** Lighting Control Station | planned | — | — | — | — | — |
| **B-ALCS** Advanced Lighting Control Station | planned | — | — | — | — | — |
| **B-ED** Elevator Display | planned | — | — | — | — | — |
| **B-EWS** Elevator Workstation | planned | — | — | — | — | — |
| **B-AEWS** Advanced Elevator Workstation | planned | — | — | — | — | — |

🚧 = in progress. ⛔ = Blocked Example (blocked on the named stack gap). "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## References

- **ANSI/ASHRAE Standard 135** (BACnet) - the protocol standard. Object model
  (Clause 12), services (Clause 15), BACnet/IP (Annex J), access control
  controller profiles (Annex L.6). Purchase / preview via the
  [ASHRAE store](https://www.ashrae.org/technical-resources/standards-and-guidelines).
- **What is BACnet?** - Chipkin's introduction:
  <https://docs.chipkin.com/protocols/bacnet/>.
- **CAS BACnet Stack** - product page and documentation:
  <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **CAS BACnet Explorer** - client for testing this device:
  <https://store.chipkin.com/products/tools/cas-bacnet-explorer>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).
- **Seed**: [BACnetProfileExample-B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP).
- **A-side peer used for wire verification**: [BACnetProfileExample-B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP).

See also [TUTORIAL.md](TUTORIAL.md), [docs/PICS.md](docs/PICS.md),
[TODO.md](TODO.md), [CHANGELOG.md](CHANGELOG.md), and [AGENTS.md](AGENTS.md).

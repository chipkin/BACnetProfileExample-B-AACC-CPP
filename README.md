# BACnet B-AACC (Advanced Access Control Controller) - C++ example

A BACnet Testing Laboratories Advanced Access Control Controller (B-AACC) device profile example,
built on the [CAS BACnet Stack](https://www.chipkin.com/cas-bacnet-stack/). Seeded from **B-ACC-CPP**
(Access Control Controller, Wave 3, released v1.0.0) and extended, not rebuilt: this repository
serves everything B-ACC-CPP serves, plus an Access User object and a set of A-side (client) keys -
see `main.cpp`'s file header for the full reasoning and every verified stack limitation this
profile ran into.

## Versions

- APP_VERSION: 1.0.0
- common/ (vendored helper): 2.5.0
- CAS BACnet Stack: 6.0.21 (`6.x` @ `abd4cee1`), linked as a STATIC library

## What is a B-AACC (Advanced Access Control Controller) profile?

An Advanced Access Control Controller is a B-ACC plus the ability to initiate requests of its own:
in addition to everything a B-ACC serves (door hardware, credential readers, Access Door/Point/
Zone/Credential/Rights, access events, scheduled unlock windows, backup/restore), a B-AACC also
reads, writes, and subscribes to other devices as a client. Annex L.6's mandatory capabilities for
a B-AACC:

| BIBB | What it means here |
|---|---|
| DS-RP-B, DS-RPM-B | Answer ReadProperty / ReadPropertyMultiple |
| DS-RP-A | **Initiate** ReadProperty - `SendReadProperty` to a peer (key 'd') |
| DS-WP-B, DS-WPM-B | Accept WriteProperty / WritePropertyMultiple |
| DS-WP-A | **Initiate** WriteProperty - `SendWriteProperty` to a peer (key 'w') |
| DS-COV-A | **Initiate** SubscribeCOV - `SendSubscribeCOV` to a peer (key 'r') |
| DS-COV-B | Answer SubscribeCOV (Bronze's Present_Value, Flax's Update_Time) |
| DS-ACAD-A | Access Control Access Doors - reads a peer door object (the A-side SendReadProperty target) |
| DS-ACCDI-A | Access Control Credential Data Input, initiate - **not implemented; see below** |
| DS-ACUC-B | Access Control Unlock Command - WriteProperty Cobalt's Present_Value |
| DS-ACSC-B | Access Control Supervisory Command - WriteProperty Copper's Authorization_Mode |
| AE-AC-B | Report access alarms/events - **see the Verify section; a real, verified stack gap** |
| AE-ACK-B, AE-INFO-B | Accept AcknowledgeAlarm, answer GetEventInformation |
| AE-EL-I-B | Event Log interface (ReadRange of Beige's Log_Buffer) |
| SCHED-I-B | Schedule/Calendar initiate (Saffron unlocks Cobalt on a schedule) |
| DM-BR-B | Backup and Restore (Ivory carries the payload) |
| DM-DDB-A,B, DM-DOB-B | Who-Is/I-Am (answer + initiate), Who-Has/I-Have |
| DM-DCC-B | DeviceCommunicationControl |
| DM-TS-B / DM-UTC-B | TimeSynchronization / UTCTimeSynchronization |
| DM-RD-B | ReinitializeDevice (also drives the backup/restore state machine) |

**DS-ACCDI-A stays unimplemented (☐).** The profile card's own note (stack issue #492) was
independently re-checked against this repo's own pinned stack source rather than assumed current -
see TODO.md #7 for the full trace. Short version: the stack's *internal* engineering issue #492 was
resolved (per the stack's own CHANGELOG, batch 104/PR #550), but the actual add/configure function
for a Credential Data Input object (`BACnetStackTestTool_AddCredentialDataInputObject`) exists only
in `CASBACnetStackTestToolDLL.h` - it is not reachable from any customer-facing build, including
this one. So the card's conclusion is still correct, just for a more specific reason than "unfixed".

## The device this example creates

| Object | Name | Notes |
|---|---|---|
| Device 389010 | Rainbow | `--deviceID` overrides |
| Analog Input 1 | Bronze | REAL, degrees Celsius; read-only; COV-subscribable |
| Binary Input 1 | Emerald | active/inactive; read-only |
| Multi-State Input 1 | Hot Pink | state 1..3; read-only |
| Access Door 1 | Cobalt | BACnetDoorValue; commandable (lock/unlock) - DS-ACUC-B, SCHED-I-B target |
| Credential Data Input 1 | Flax | AuthenticationFactor; Update_Time COV-subscribable |
| Access Point 1 | Copper | Access_Event demo target; Authorization_Mode writable (DS-ACSC-B) |
| Access Zone 1 | Ebony | Occupancy_State |
| Access Credential 1 | Coral | Credential_Status |
| Access Rights 1 | Cyan | Enable; Global_Identifier writable |
| **Access User 1** | **Denim** | **New in this profile.** User_Type; Global_Identifier writable; Credentials unserved (see TODO.md #2) |
| Event Log 1 | Beige | AE-EL-I-B |
| Schedule 1 | Saffron | writes Cobalt at priority 12 |
| Calendar 1 | Cream | Date_List not populatable (inherited gap, see TODO.md) |
| File 1 | Ivory | stream access, backup/restore payload |
| Notification Class 1 | Crimson | routes Copper's alarms (see TODO.md #1) |
| Network Port 1 | Vermilion | BACnet/IP |

## A-side (client) keys

New in this profile, on top of everything B-ACC-CPP serves. This device also **initiates**
requests against a peer device - a separately-built, separately-run local instance of
[BACnetProfileExample-B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP)
(device 389011 "Rainbow", Access Door 1 "Cobalt"), not modified by this repository:

| Key | Service | Target |
|---|---|---|
| `d` | `SendReadProperty` (DS-RP-A) | peer's Access Door 1 (Cobalt) `Present_Value` |
| `w` | `SendWriteProperty` (DS-WP-A) | peer's Access Door 1 (Cobalt) `Present_Value` (toggles lock/unlock, priority 8) |
| `r` | `SendSubscribeCOV` (DS-COV-A) | peer's Access Door 1 (Cobalt), 300s lifetime, confirmed notifications |

All three also fire once automatically at start-up, so a scripted/headless run (no interactive
keyboard) still exercises the A-side without a human pressing a key. The peer's IP/port default to
`127.0.0.1:47809`; override with `--peerIp <a.b.c.d>` / `--peerPort <n>`.

**A known limitation, not a functional break** (TODO.md #8): the CAS BACnet Stack's
customer-facing API has no callback to observe a received ReadProperty-Ack, WriteProperty
SimpleAck, or COV notification in-process - grepped `CASBACnetStackDLL.h` at the pin, zero hits.
This file's own console therefore only confirms a `Send*` call was *accepted by the local stack for
transmission*, not that a reply arrived; the actual round trip is verified independently on the
wire (see Verify below).

## What this example does NOT do yet

See `TODO.md` for the full, wire-verified list with filed stack issues. Summary (items 1, 3-6
carried forward unchanged from B-ACC-CPP; items 2 and 7-8 are new to or extended by this profile):

1. **AE-AC-B alarm generation is not implementable through the customer API at this pin.**
   [chipkin/cas-bacnet-stack#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044)
2. Several REQUIRED constructed-type properties have no customer-facing Get callback, now
   including Access User's `Credentials` (`BACnetLIST of BACnetDeviceObjectReference`).
   [chipkin/cas-bacnet-stack#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046)
3. **Adding an Event Log object causes a continuous, non-fatal internal log flood** (carried
   forward from B-ACC-CPP; re-verification of this repo's own build is in the Verify section).
   [chipkin/cas-bacnet-stack#2045](https://github.com/chipkin/cas-bacnet-stack/issues/2045)
4. A live WriteProperty to Copper's `Access_Event` currently answers `Error(unknown-object)`.
5. A live `AtomicReadFile` against Ivory during an active backup session aborted.
6. Cream's `Date_List` cannot be populated (stack issue #963, same as B-AAC/B-ACC).
7. **DS-ACCDI-A is not implementable through the customer API** - re-confirmed against this
   repo's own pin, not assumed from the card. See TODO.md #7.
8. The A-side `Send*` calls have no customer-facing way to observe the peer's reply in-process.
   See TODO.md #8.

## Before you ship

Change `VENDOR_IDENTIFIER`, `VENDOR_NAME`, `MODEL_NAME`, `DEVICE_DESCRIPTION`, and pick a real
`DCC_PASSWORD` if you need one. See `main.cpp`'s "Device identity" block.

## Requires the CAS BACnet Stack (licensed product)

This example links the [CAS BACnet Stack](https://www.chipkin.com/cas-bacnet-stack/), a
commercially licensed product, as a git submodule (`submodules/cas-bacnet-stack`, private - your
GitHub account needs read access, or CI's `CAS_STACK_PAT` secret). It is not included by this
CC0-licensed example itself.

## Link mode: STATIC

This example builds against a prebuilt static library (`CASBACnetStack_x64_Release.lib` /
`libCASBACnetStack_x64_Release.a`), built by the stack's own project files via
`tools/build-stack-static.sh`. The adapter also offers a SOURCE mode as a fallback (compiling the
stack's `source/` directly into the executable); this example is not shipped that way.

## Build

```bash
# from the series root (one level up from this repo)
tools/build-stack-static.sh BACnetProfileExample-B-AACC-CPP
```

```powershell
cd BACnetProfileExample-B-AACC-CPP
cmake -B build -S . -DCAS_BACNET_STACK_LINK=STATIC
cmake --build build --config Release
```

Expected output:

```
BACnet Advanced Access Control Controller (B-AACC) Example - C++ v1.0.0
CAS BACnet Stack version: 6.0.21.0
Common helper (common/) version: 2.5.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
FYI: Device 389010 ("Rainbow") ready. Vendor ID 389. Press 'h' for help.
FYI: A-side peer target 127.0.0.1:47809 (override with --peerIp/--peerPort). Keys: 'd' SendReadProperty, 'w' SendWriteProperty, 'r' SendSubscribeCOV - all to the peer's Access Door 1.
```

### Two-instance test setup (this device + its A-side peer)

```bash
# Terminal 1: the peer (B-ACDC-CPP, unmodified, its own default port)
cd BACnetProfileExample-B-ACDC-CPP
./build/BACnetExampleBACDC --port 47809

# Terminal 2: this device
cd BACnetProfileExample-B-AACC-CPP
./build/BACnetExampleBAACC --port 47808 --peerPort 47809
```

## Verify

See TODO.md for the full gap list and TODO.md #9 for the raw session log excerpts. Verified live
this session, real processes only (this repository's own build, a real separately-built local
B-ACDC-CPP instance as the A-side peer, and `bacpypes3` as an independent third-party client) -
anything not explicitly listed below as verified is unverified, not assumed working:

- Who-Is / I-Am from 389010, and ReadProperty of the base objects and the inherited B-ACC-CPP
  object set (same code path B-ACC-CPP already verified live).
- **Access User 1 (Denim)**, read with `bacpypes3` directly against this device: `Object_Name` =
  `"Denim"`; `Global_Identifier` read `0`, `WriteProperty <- 4242`, read back `4242`; `User_Type` =
  `asset` (stack's own generic default, as documented); `Reliability` = `no-fault-detected`.
- **SendReadProperty** (DS-RP-A, key 'd'): peer answered with a real ReadProperty-Ack, observed on
  this device's own console (`RX 20 bytes from 127.0.0.1:47809`). Confirmed working.
- **SendWriteProperty** (DS-WP-A, key 'w'): the *peer's own console* logged
  `WriteProperty: Access Door 1 (Cobalt) <- unlock @ priority 8  (door is now unlock)` - the peer's
  door object genuinely changed state. Confirmed working.
- **SendSubscribeCOV** (DS-COV-A, key 'r'): correctly formed and sent, but the peer answered
  `Error: Services is not supported service=[5]` - B-ACDC-CPP deliberately does not implement
  SubscribeCOV at all (its own README/main.cpp say so). The *request* path is confirmed working;
  a live subscription against this specific peer object is not achievable, because the peer the
  card specifies as the target doesn't support the service under test. See TODO.md #9.
- **Event Log flood (TODO.md #3 / #2045)**: reproduced identically in this repo's own build
  (`BACnetDateTime::operator=() ... Failed to set the date/time`, continuous from start-up) -
  confirms the gap is not specific to B-ACC-CPP's own binary.
- **DS-ACCDI-A (TODO.md #7)**: confirmed unimplementable by direct source inspection at this
  repo's own pin (not a live-wire test, since there is no customer-facing way to even construct
  the object to test against).

## What's in this repository

- `main.cpp` - the example itself.
- `CMakeLists.txt` - build configuration (STATIC link).
- `common/` - the series' vendored helper (UDP transport, time sync, keyboard, version banner).
- `submodules/cas-bacnet-stack` - the CAS BACnet Stack (git submodule, private).
- `docs/objects.json` - source for the generated Objects and properties block below.
- `TODO.md` - every known gap, verified against the pin and/or the wire, with filed stack issues
  (carried forward from B-ACC-CPP plus this profile's own delta).
- `.github/workflows/release.yml` - CI: build + smoke test on every push; publish binaries and
  `metrics.json` on a `v*.*.*` tag.

## Objects and properties

<!-- OBJECTS-PROPERTIES:BEGIN (generated by tools/gen-objects-properties.py from docs/objects.json - do not edit here) -->
Every object this example creates, and every REQUIRED property of each (per ANSI/ASHRAE 135-2024 clause 12 and the stack's `docs/property-profile-reference.md`), plus the optional properties the example turns on. **Served by** says who answers a ReadProperty: the **stack** generates it, or the **app** serves it from a `GetProperty*` callback in `main.cpp`. A ⚠ row is a required property the app does not serve and the stack would fill with a default - that is a defect, not a feature.

### Analog Input 1 "Bronze" - REAL, degrees Celsius; starts at 21.5. Present_Value is DS-COV-B subscribable; the up/down key feeds subscribers via BACnetStack_UpdateValue

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |

### Binary Input 1 "Emerald" - starts active

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |

### Multi-state Input 1 "Hot Pink" - state 1 of 3: On, Off, Auto

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| State_Text *(optional, enabled)* | BACnetARRAY[N] of CharacterString | app | no |

### Access Door 1 "Cobalt" - DS-ACUC-B (canonical: B-ACDC). commandable BACnetDoorValue (lock/unlock); 16-slot Priority_Array, Relinquish_Default lock(0); Door_Status/Lock_Status/Secured_Status derived from the effective Present_Value. WriteProperty-verified on the wire: unlock -> Present_Value=unlock, Lock_Status=unlocked. Also SCHED-I-B's write target (Saffron)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetDoorValue | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalDoorValue | stack | no |
| Relinquish_Default | BACnetDoorValue | app | no |
| Door_Status *(optional, enabled)* | BACnetDoorStatus | app | no |
| Lock_Status *(optional, enabled)* | BACnetLockStatus | app | no |
| Secured_Status *(optional, enabled)* | BACnetDoorSecuredStatus | app | no |
| Door_Pulse_Time | Unsigned | app | no |
| Door_Extended_Pulse_Time | Unsigned | app | no |
| Door_Open_Too_Long_Time | Unsigned | app | no |

### Credential Data Input 1 "Flax" - canonical pattern: B-ACCR. AuthenticationFactor (weigand demo badge) via GetPropertyOctetString + GetPropertyAuthenticationFactorFormat for Supported_Formats; Update_Time (NOT Present_Value) is DS-COV-B subscribable, per B-ACCR's file header. WriteProperty-verified: RP returns a real AuthenticationFactor and Update_Time=08:00:00.00 at start-up

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetAuthenticationFactor | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |

### Access Point 1 "Copper" - AE-AC-B / DS-ACSC-B. VERIFIED GAP (TODO.md #1, chipkin/cas-bacnet-stack#2044): SetIntrinsicAccessEventAlgorithm/SetAccessEventContext are test-tool-only, AND the generic SetIntrinsicChangeOfStateAlgorithmUnsigned substitute rejects objectType=accessPoint - confirmed by calling it. So no intrinsic engine is armed here and no notification is produced; Access_Event is a plain read/write property only. VERIFIED GAP (TODO.md #2/#4, chipkin/cas-bacnet-stack#2046): Access_Event_Time/Access_Event_Credential have no servable path (BACnetTimeStamp/BACnetDeviceObjectReference, no typed callback); a live WriteProperty to Access_Event currently answers Error(unknown-object) rather than reaching this file's callback - root cause not found in the time available. Authorization_Mode write (DS-ACSC-B supervisory command) verified accepted at start-up (authorize/denyAll)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Authentication_Status | BACnetAuthenticationStatus | app | no |
| Active_Authentication_Policy | Unsigned | app | no |
| Number_Of_Authentication_Policies | Unsigned | app | no |
| Authorization_Mode | BACnetAuthorizationMode | app | yes |
| Access_Event | BACnetAccessEvent | app | yes |
| Access_Event_Tag | Unsigned | app | no |
| Access_Event_Time | BACnetTimeStamp | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Access_Event_Credential | BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Access Zone 1 "Ebony" - Occupancy_State (normal) wire-verified. VERIFIED GAP (TODO.md #2, chipkin/cas-bacnet-stack#2046): Entry_Points/Exit_Points (required BACnetLIST of BACnetDeviceObjectReference) have no servable path on the customer surface - same class of gap as Access Credential/Rights below, not individually wire-tested this session

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Global_Identifier | Unsigned32 | app | yes |
| Occupancy_State | BACnetAccessZoneOccupancyState | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Entry_Points | BACnetLIST of BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Exit_Points | BACnetLIST of BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Access Credential 1 "Coral" - Credential_Status (active) wire-verified. VERIFIED GAP (TODO.md #2, chipkin/cas-bacnet-stack#2046): Authentication_Factors (required BACnetARRAY of BACnetCredentialAuthenticationFactor) answers Abort(other) on live ReadProperty - confirmed on the wire, not assumed. Activation_Time/Expiration_Time (BACnetDateTime) and Assigned_Access_Rights (BACnetARRAY of BACnetAssignedAccessRights) share the same no-typed-callback gap, not individually wire-tested

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Global_Identifier | Unsigned32 | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Credential_Status | BACnetBinaryPV | app | no |
| Reason_For_Disable | BACnetLIST of BACnetAccessCredentialDisableReason | app | no |
| Authentication_Factors | BACnetARRAY[N] of BACnetCredentialAuthenticationFactor | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Activation_Time | BACnetDateTime | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Expiration_Time | BACnetDateTime | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Credential_Disable | BACnetAccessCredentialDisable | app | no |
| Assigned_Access_Rights | BACnetARRAY[N] of BACnetAssignedAccessRights | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Access Rights 1 "Cyan" - Enable (true) wire-verified. VERIFIED GAP (TODO.md #2, chipkin/cas-bacnet-stack#2046): Negative_Access_Rules answers Abort(other) on live ReadProperty (required BACnetARRAY of BACnetAccessRule, no typed callback); Positive_Access_Rules shares the same gap

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Global_Identifier | Unsigned32 | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Enable | Boolean | app | no |
| Negative_Access_Rules | BACnetARRAY[N] of BACnetAccessRule | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Positive_Access_Rules | BACnetARRAY[N] of BACnetAccessRule | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Access User 1 "Denim" - Profile delta object (B-AACC only, not in B-ACC-CPP). Object_Name/Global_Identifier (writable) wire-verified. Reliability/User_Type left to the stack's own documented generic defaults (property-profile-reference.md: both "Generic Enumerated default: 0"), not app-served. VERIFIED GAP (TODO.md #2, chipkin/cas-bacnet-stack#2046): Credentials (required BACnetLIST of BACnetDeviceObjectReference) has no customer-facing Get callback - same gap class as Access Credential/Rights' constructed-type properties, independently re-confirmed against this repo's own pin

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Global_Identifier | Unsigned32 | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| User_Type | BACnetAccessUserType | stack default, accepted (Generic Enumerated default: `0`) | no |
| Credentials | BACnetLIST of BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Event Log 1 "Beige" - AE-EL-I-B. Added with BACnetStack_AddEventLogObject; Property_List/Status_Flags are stack-generated (accepted here only because the generic table does not credit AddEventLogObject's own storage), Event_State/Enable are the object's stack-held defaults (Enable left off - this example generates no notifications for it to capture, per TODO.md #1). Record_Count=0 wire-verified. VERIFIED DEFECT (TODO.md #3, chipkin/cas-bacnet-stack#2045): adding this object alone causes a continuous, non-fatal 'Failed to set the date/time' internal log flood from Tick 1 - isolated by bisection, independent of every other object in this file

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Enable | Boolean | stack default, accepted (Generic Boolean default: `false`) | no |

### Schedule 1 "Saffron" - SCHED-I-B (canonical pattern: B-AAC). Writes Cobalt's Present_Value (BACnetDoorValue, datatype 9=Enumerated) at priority 12: unlock weekdays 08:00, lock the rest of the time (Schedule_Default), plus one 2026-12-25 lock exception (inline calendar-Date form - see Cream's note). All Schedule-owned properties are genuinely populated by BACnetStack_AddScheduleObject/AddScheduleWeeklyTimeValue/SetScheduleDefault/etc at start-up; marked accepted only because the generic table does not credit this object-specific host-configuration API

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Any | stack default, accepted (Stack-generated if commandable (resolves the priority array)) | no |
| Effective_Period | BACnetDateRange | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Schedule_Default | Any | stack | no |
| List_Of_Object_Property_References | BACnetLIST of BACnetDeviceObjectPropertyReference | stack | no |
| Priority_For_Writing | Unsigned(1..16) | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |

### Calendar 1 "Cream" - Same inherited gap B-AAC's file header documents against stack issue #963: no customer-facing way to populate Date_List. Saffron's one exception uses the inline calendar-Date form instead of a Cream reference, so this gap does not affect Saffron's own behaviour

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Boolean | app | no |
| Date_List | BACnetLIST of BACnetCalendarEntry | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### File 1 "Ivory" - DM-BR-B backup/restore payload carrier - stream access, in-memory 4KB buffer via BACnetStack_RegisterCallbackReadFile/WriteFile. File_Type/File_Size/Modification_Date/Archive/Read_Only all have NO stack default per property-profile-reference.md and are all served here. File_Size=0 wire-verified. VERIFIED GAP (TODO.md #5, chipkin/cas-bacnet-stack#2046): a live AtomicReadFile against this object aborted (Abort(other)) during an active backup session - not root-caused in the time available. Backup_And_Restore_State transitions wire-verified: idle -> performing-abackup (ReinitializeDevice startBackup accepted) -> idle (endBackup accepted)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| File_Type | CharacterString | app | no |
| File_Size | Unsigned | app | no |
| Modification_Date | BACnetDateTime | app | no |
| Archive | Boolean | app | yes |
| Read_Only | Boolean | app | no |
| File_Access_Method | BACnetFileAccessMethod | stack | no |

### Notification Class 1 "Crimson" - Genuinely populated by BACnetStack_AddNotificationClassObject/AddRecipientToNotificationClass at start-up (same convention as B-LSC's Crimson); accepted only because the generic table cannot credit that host-configuration API. Currently unused for alarm routing given TODO.md #1's finding (no algorithm can be armed on Copper) - kept in the object model because AddRecipientToNotificationClass/SetAlarmsAndEventsForObjectEnabled were still exercised and returned success

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Priority | BACnetARRAY[3] of Unsigned | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Ack_Required | BACnetEventTransitionBits | stack default, accepted (Generic BitString default: empty bitstring (zero bits - NOT ) | no |
| Recipient_List | BACnetLIST of BACnetDestination | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Network Port 1 "Vermilion" - BACnet/IP; Network_Type and Protocol_Level are set from BACnetStack_AddNetworkPortObject()'s arguments at start-up; Changes_Pending is computed and answered natively by the stack. Reliability has no fault condition this example detects, so it is accepted at the generic default (normal)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Network_Type | BACnetNetworkType | app | no |
| Protocol_Level | BACnetProtocolLevel | app | no |
| Changes_Pending | Boolean | app | no |

<!-- OBJECTS-PROPERTIES:END -->

## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
The CAS BACnet Stack supports every standardized device profile in ASHRAE 135-2024 Annex L. One example repository per profile shows how. ✅ = the required BIBB (service) is supported by the CAS BACnet Stack; the **Example** column is the state of that profile's tutorial repository.

### Controllers (Annex L.4)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) ✅ | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) ✅ · [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-CRL-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) 📝 | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-RPM-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-CRL-B · ✅ SCHED-E-B · ✅ T-VMT-I-B · ✅ T-ATR-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Life safety controllers (Annex L.5)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ AE-LS-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ AE-LS-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |

### Access control controllers (Annex L.6)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-ACUC-B · ✅ DS-ACSC-B · ✅ AE-AC-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) 📝 | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-RPM-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-A · ✅ DS-COV-B · ✅ DS-ACAD-A · ☐ DS-ACCDI-A · ✅ DS-ACUC-B · ✅ DS-ACSC-B · ✅ AE-AC-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Lighting controllers (Annex L.11)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-LO-B / DS-BLO-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WG-E-B · ✅ DS-ALO-A · ✅ SCHED-E-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |

### Elevator controllers (Annex L.13)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-OCD-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Authentication and authorization (Annex L.14)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) 🚧 | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ AA-AS-B |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ NM-BBMDC-B |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-ACAD-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-COV-B · ✅ DS-ACCDI-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-A · ✅ DM-DOB-B · ☐ DM-LM-B · ✅ NM-RC-B |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ GW-EO-B / GW-VN-B |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DAB-B |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) 📝 | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ NM-SCH-B |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12) — client-side profiles

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) ✅ | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-V-A · ✅ DS-M-A · ✅ AE-N-A · ✅ AE-VN-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-OWS** Operator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-V-A · ✅ DS-M-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-VM-A · ✅ AE-VN-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-MTS-A |
| **B-AWS** Advanced Operator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-AV-A · ✅ DS-AM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-AVM-A · ✅ AE-AVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ DM-DDA-A · ✅ NM-CC-A · ✅ AR-AVM-A |
| **B-XAWS** Extended Advanced Operator Workstation | planned | ✅ union of B-AWS + B-AACWS + B-ALWS + B-AEWS |
| **B-LSAP** Life Safety Annunciator Panel | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LSV-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-LSVN-A |
| **B-LSWS** Life Safety Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LSV-A · ✅ DS-LSM-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-LSVM-A · ✅ AE-LSAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-ALSWS** Advanced Life Safety Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LSAV-A · ✅ DS-LSAM-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-LSAVM-A · ✅ AE-LSAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ AR-AVM-A |
| **B-ACSD** Access Control Security Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACV-A · ✅ DS-ACM-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-MTS-A |
| **B-ACWS** Access Control Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACAV-A · ✅ DS-ACM-A · ✅ DS-ACUC-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACVM-A · ✅ AE-ACAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-AACWS** Advanced Access Control Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACAV-A · ✅ DS-ACAM-A · ✅ DS-ACUC-A · ✅ DS-ACSC-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACAVM-A · ✅ AE-ACAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ AR-AVM-A |
| **B-LOD** Lighting Operator Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LV-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ALWS** Advanced Lighting Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LAV-A · ✅ DS-LAM-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-AVM-A · ✅ AE-AVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-LCS** Lighting Control Station | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LO-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-ALCS** Advanced Lighting Control Station | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ SCHED-E-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-ED** Elevator Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-EV-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-EVN-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-EWS** Elevator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-COVM-A · ✅ DS-EV-A · ✅ DS-EM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-EVM-A · ✅ AE-EAVN-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A |
| **B-AEWS** Advanced Elevator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-COVM-A · ✅ DS-EAV-A · ✅ DS-EAM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-EAVM-A · ✅ AE-EAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |

Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## Footprint

Recorded by CI on the first successful build/release; see `.github/workflows/release.yml`'s
`metrics.json` artifact.

## References

- [ANSI/ASHRAE 135-2024](https://www.ashrae.org/technical-resources/bookstore/bacnet) (BACnet), Annex L.6.
- CAS BACnet Stack documentation, `submodules/cas-bacnet-stack/docs/`.
- Series bible: `../docs/series-runbook.md`.
- Seed: [BACnetProfileExample-B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP).
- A-side peer used for wire verification: [BACnetProfileExample-B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP).

## Use this in your own project

This example's `main.cpp`, `CMakeLists.txt`, and `common/` are CC0 (public domain) - see LICENSE.
The CAS BACnet Stack itself is a separate, commercially licensed product.

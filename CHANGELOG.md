# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-11-02

Built on CAS BACnet Stack 6.x (`1e7dffe2b`).

This is still a **Blocked Example**, blocked on
[chipkin/cas-bacnet-stack#2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150)
and [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044). It makes
no grant or deny decision and generates no access-event notification.

### Changed

- **CAS BACnet Stack updated** to 6.x (`1e7dffe2b`). At this version the stack
  no longer gives the example an address for a broadcast it sends on its own,
  such as the I-Am that answers a Who-Is; the vendored helper chooses it (next
  item). An Access Credential's `Assigned_Access_Rights` and
  `Authentication_Factors`, an Access Rights object's `Positive_Access_Rules`
  and `Negative_Access_Rules`, and an Access Point's `Access_Doors` now read as
  an empty list instead of Error unknown-property; the example still cannot
  fill them (#2150).
- **Vendored `common/` updated to 3.6.1.** A broadcast the stack sends without
  a destination address (a network layer message, or an unconfirmed I-Am or
  I-Have) is broadcast on the subnet and also sent unicast to the last client
  heard from on another UDP port of the same host, so a tool running beside
  the example still hears the answer. Event notifications and BBMD-forwarded
  messages are not copied. See `common/CHANGELOG.md`.
- **VeriBACnet project** (`tests/veribacnet/`): the EPICS no longer gives a
  fixed state for Access Door 1, whose state follows the Schedule.
- **README**: the five authorization-data properties are described as they
  read at this stack version; the profile example table is the same in every
  example, with the five blocked examples marked with their open stack issue.
- **TODO.md** brought up to date for this version.

## [1.1.0] - 2026-10-27

This is a **Blocked Example**. The CAS BACnet Stack cannot yet perform the full
B-AACC Profile Function (ANSI/ASHRAE 135-2024 L.6.1) through its customer
interface. See the note at the top of the README.

- **Does today:** serves everything B-ACC-CPP serves plus an Access User object,
  and sends ReadProperty, WriteProperty and SubscribeCOV to a peer device's door.
- **Does not do today:** the authorization data (Access Credential, Access Rights
  and Access Point rule and door lists) cannot be served, no access-event
  notification can be generated, and replies to the requests it sends cannot be
  consumed. It makes no grant or deny decision. The PICS therefore does not claim
  DS-ACUC-B, DS-ACSC-B, AE-AC-B or AE-EL-I-B.

Built on CAS BACnet Stack 6.x (`69b6249f`).

### Added

- **Automated self-tests** under `tests/`: a discovery test that reads every
  property of every object, plus time-synchronization and recipient-list tests.
- **`--deviceName <text>`** sets the Device's `Object_Name` at start-up. The
  default is unchanged and the name cannot be written over BACnet. `--help` now
  lists only the options this example reads.
- **TUTORIAL.md** (extending the example, troubleshooting) and **docs/PICS.md**
  (Annex A style, including the client-side initiate and execute split).

### Changed

- **Device renamed** from "Rainbow" to "Chipkin Example B-AACC" so examples on one
  network can be told apart. Object names such as "Bronze" are unchanged.
- **Build now compiles the stack source directly into the executable**:
  `cmake -B build -S .` then `cmake --build build --config Release` on every
  platform; the separate static-library step is gone.
- **Protocol_Revision is 30** and segmentation is `segmented-both`.
- **BIBB claims corrected** against Annex K, as listed above. DS-ACAD-A and
  DS-COV-A are not claimed and DS-RP-A is partial. The peer device is named
  "Chipkin Example B-ACDC".
- **Database_Revision reads 16** in the PICS (the stack counts the objects added
  at start-up, cl. 12.11).
- **Notification Class 1 `Recipient_List` is writable.** The default entry is the
  single local-broadcast recipient with Process Identifier 0 (cl. 12.21) and
  returns at restart.
- **Access Point 1 `Access_Event_Credential`** now reads as the "no credential"
  reference (cl. 12.31.30) instead of an error.

### Fixed

- **Access Door 1 now accepts pulse-unlock and extended-pulse-unlock** commands
  (cl. 12.26.16, 12.26.17) and relinquishes them after the pulse time. The door
  timings are now 3.0 s, 10.0 s and 3.0 s.
- **TimeSynchronization and UTCTimeSynchronization set the device clock.**
  Previously they were acknowledged but ignored.
- **SubscribeCOV accepts lifetimes up to 8 hours** (was refused above 1 hour).
- **Analog Input 1 has `COV_Increment`** (1.0), as cl. 12.2 requires for COV.
- **Device `Local_Date` and `Local_Time` are served**, so Schedule 1 now evaluates
  and drives the door.
- **Credential Data Input 1 `Supported_Formats`** is served and lists
  simple-number32 (it previously listed an invalid format).
- **Application_Software_Version and Firmware_Revision** report the real build
  version and stack version instead of a fixed "1.0.0".
- **Requests no longer go unanswered on Windows** in rare timing cases (shared
  `common/` 3.5.0, which also adds the `--deviceName` helper).
- **PICS** lists the COV notification services the device sends.

## [1.0.0] - 2026-09-15

### Added

- Initial **B-AACC (Advanced Access Control Controller)** profile example in C++,
  extending B-ACC-CPP. Built on CAS BACnet Stack 6.x (`abd4cee1`, 6.0.21).
- Supports DS-RP-B, DS-RPM-B, DS-WP-B, DS-WPM-B, DS-COV-B, SCHED-I-B, DM-BR-B,
  DM-DDB-A/B, DM-DOB-B, DM-DCC-B, DM-TS-B, DM-UTC-B, DM-RD-B, AE-ACK-B and
  AE-INFO-B.
- Objects: the B-ACC set (sensors, Access Door, Credential Data Input, Access
  Point, Access Zone, Access Credential, Access Rights, Event Log, Schedule,
  Calendar, File, Notification Class, Network Port) plus Access User 1 "Denim".
- Client keys 'd', 'w' and 'r' send ReadProperty, WriteProperty and SubscribeCOV
  to a peer device (a local B-ACDC-CPP instance), and fire once at start-up.

### Known gaps

- Access-event notifications (AE-AC-B) cannot be generated, and several
  access-family list properties, including Access User `Credentials`, cannot be
  served. Credential Data Input (DS-ACCDI-A) is not implemented.
- Replies to the client requests cannot be observed in-process.

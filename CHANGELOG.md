# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - unreleased

### Changed

- **Labelled a Blocked Example.** The B-AACC Profile Function (authentication
  and authorization for physical access, configured through the Access User,
  Access Credential and Access Rights objects, using remote door controllers
  and readers, and reported as access events; ANSI/ASHRAE 135-2024 L.6.1) cannot be performed through the stack's customer
  interface: the authorization-data properties cannot be served
  ([stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150)) and
  no ACCESS_EVENT notification can be generated
  ([stack #2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044)). The
  stack owner ruled on 2026-10-15 that neither is promoted for now. README,
  PICS, TODO.md, `main.cpp` and the Device's `Description` say so.
- **BIBB claims corrected** (verified against 135-2024 Annex K): DS-ACUC-B is
  "Access Control User Configuration" (K.1.34) and DS-ACSC-B is "Access Control
  Site Configuration" (K.1.36) - reading and writing the standard properties of
  the access objects - not "Unlock Command" / "Supervisory Command"; both are
  now **not claimed** (#2150). AE-EL-I-B (K.2.21) is not claimed: nothing is
  logged because no notification is generated. The README, TODO.md and
  TUTORIAL no longer say a `changeOfState` notification is produced as an
  AE-AC-B substitute (the stack rejects that algorithm for an Access Point; no
  notification of any kind is produced). DS-ACAD-A (K.1.37: all forms of all
  standard Access Door properties) is not claimed - only the peer door's
  Present_Value is touched; DS-COV-A is not claimed - it has never succeeded
  and notifications cannot be received; DS-RP-A is partial - the reply cannot
  be consumed. The peer is device 389011 "Chipkin Example B-ACDC" (was named
  "Chipkin Example B-AACC"). PICS: SCHED-I-B is "Internal", Who-Is is
  initiated at start-up. Annex L.6 -> L.6.1.
- **Stack Pin moved to `6.x` @ `64b2cfac5` (6.0.23)** from `abd4cee1` (6.0.21).
  Re-checked on the wire: the Event Log log flood (#2045), the Access_Event
  write (#2151) and File_Size (#2152) are fixed. DS-ACCDI-A: the stack's
  Credential Data Input exports are still test-tool only (#492 closed). Calendar exports (#963) are
  now on the customer interface; Cream does not use them yet (TODO.md #3).
- **Protocol_Revision 24 -> 30** (stack default at the pin); segmentation is
  now `segmented-both` (stack #2992).
- **`common/` 3.0.0 -> 3.3.0**, copied verbatim from B-SS-CPP `b640a81`.

### Fixed

Found by the new discovery Wire Test at the new pin:

- The Device's `Local_Date` and `Local_Time` answered read-access-denied: the
  stack lists them (the device executes TimeSynchronization and
  UTCTimeSynchronization) but the Date/Time callbacks never served them. They
  now answer wall-clock local time.
- Schedule 1 ("Saffron")'s `Present_Value` answered value-not-initialized,
  because the stack's Schedule engine runs on the Device's `Local_Date` /
  `Local_Time`. With them served, Saffron evaluates and writes Cobalt.
- Credential Data Input 1 ("Flax")'s `Supported_Formats` answered
  unknown-property: the array length (index 0) was never served. It is now,
  as in B-ACCR.

### Added

- **Discovery Wire Test** (`tests/discovery_test.py`, `tests/run_wire_tests.py`,
  from B-SS-CPP `da3e96f`, with this example's 17-object control list): reads
  every property in every object's Property_List. Two additions: Event Log
  `Log_Buffer` must answer read-access-denied (ReadRange only, cl. 12.27.13),
  and the six #2150 properties are reported as `[KNOWN GAP]`s. 24/24 with 6
  known gaps on Windows and Linux. CI runs it on Linux after the smoke test.
- `wiretest/` 0.5.0, vendored verbatim from B-BBMD-CPP `75aedd8`.

## [1.0.2] - unreleased

### Changed

- **Device renamed from the series' colour placeholder "Rainbow" to "Chipkin
  Example B-AACC"** so devices from different examples in the series are
  distinguishable from each other on the same BACnet network - every example
  previously announced the identical Object_Name "Rainbow", which made two
  examples on one subnet indistinguishable by name. Sub-object names (Analog
  Input 1 "Bronze", etc.) are unchanged - only the Device object's name
  changed. `docs/colour-table.md` (series root) updated to match. APP_VERSION
  bumped 1.0.1 -> 1.0.2.

## [Unreleased]

### Fixed

- **`Application_Software_Version` (12) and `Firmware_Revision` (44) were
  hardcoded and stale** - the same bug found and fixed in the sibling
  BACnetProfileExample-B-SCHUB-CPP example via a real device read (BACnet
  Explorer): `Application_Software_Version` reported a hardcoded `"1.0.0"`
  regardless of the actual build, and `Firmware_Revision` was the same stale
  `"1.0.0"` constant - it was never meant to be this example's own version at
  all, it names the underlying platform. Fixed: `Application_Software_Version`
  now reads `APP_VERSION` directly (one source of truth, can't drift from
  `--version`'s own banner again). `Firmware_Revision` is now built at
  runtime from the CAS BACnet Stack's own `BACnetStack_GetAPIMajorVersion()`/
  `GetAPIMinorVersion()`/`GetAPIPatchVersion()`/`GetAPIBuildVersion()` (the
  same 4 calls `common/CASExampleHelper.cpp`'s `PrintVersion()` already uses
  for the startup banner), populated once right after `LoadBACnetFunctions()`
  succeeds. APP_VERSION bumped 1.0.0 -> 1.0.1.

### Changed

- Restructured the documentation to match the series' new shape (matching
  `BACnetProfileExample-B-SS-CPP`): `README.md` is cut down to this example
  only (series framing, generic profile explanation, the old "Before you
  ship" table, "Get the code", "Link mode", "Troubleshooting", "Extending the
  example", and the inline "Objects and properties" table all removed or
  moved out), with a new **[TUTORIAL.md](TUTORIAL.md)** (extending the
  example, what each object needs served, a worked served-by breakdown for
  Access Door 1 "Cobalt", reviewing your device, and troubleshooting - every
  gap carried forward precisely from `TODO.md`) and a new
  **[docs/PICS.md](docs/PICS.md)** (ANSI/ASHRAE 135 Annex A shape, with the
  A-side initiate/execute split this profile needs).
- `docs/objects.json` now includes the Device object (previously omitted
  from the generated tables), so `docs/PICS.md`'s objects-and-properties
  section documents all seventeen objects, not sixteen. Regenerating
  produced zero ⚠ rows.
- **Build changed from STATIC to the adapter's default SOURCE mode**: the
  stack's `source/` now compiles straight into the executable, so
  `tools/build-stack-static.sh` and the `-DCAS_BACNET_STACK_LINK=STATIC`
  flag are no longer part of the documented build - it is now
  `cmake -B build -S .` / `cmake --build build --config Release` on every
  platform, identical to the rest of the series.
  `.github/workflows/release.yml` no longer builds or caches a prebuilt
  static library or carries per-OS `lib:` matrix entries; it asserts
  `CAS_BACNET_STACK_LINK:STRING=SOURCE` instead of `STATIC`, records
  `"link_mode": "SOURCE"` in `metrics.json`, and packages `TUTORIAL.md` and
  `docs/PICS.md` alongside the binary. No footprint numbers have been
  published yet, so there is nothing stale to refresh.
- `main.cpp`'s `CHANGE ALL OF THIS BEFORE YOU SHIP` block now carries the
  per-field ship guidance that used to live in the README's table, including
  the `DEVICE_NAME` uniqueness warning and a note on picking a real
  `DCC_PASSWORD`.
- `AGENTS.md` updated to describe the new file layout, the SOURCE-mode
  build, and a PICS-regeneration verification step.

## [1.0.0] - 2026-09-15

### Added

- Initial **B-AACC (Advanced Access Control Controller)** profile example for
  the CAS BACnet Stack in C++. Seeded from **B-ACC-CPP** (Wave 3, released
  v1.0.0), extending it rather than rebuilding from scratch: everything
  B-ACC-CPP serves, plus this profile's own delta. Pinned to the CAS BACnet
  Stack `6.x` branch at `abd4cee1` (reports 6.0.21), linked as a **STATIC**
  library; vendors `common/` 2.5.0 (copied verbatim from B-SS-CPP).
- Implements DS-RP-B, DS-RPM-B, DS-WP-B, DS-WPM-B, DS-COV-B, DS-ACUC-B,
  DS-ACSC-B, AE-ACK-B, AE-INFO-B, AE-EL-I-B, SCHED-I-B, DM-BR-B, DM-DDB-A/B,
  DM-DOB-B, DM-DCC-B, DM-TS-B/DM-UTC-B, DM-RD-B (all inherited from B-ACC-CPP
  unchanged), plus this profile's own delta:
  - **Access User 1 "Denim"** (new object; `Object_Name`/`Global_Identifier`
    served and writable; `Reliability`/`User_Type` on the stack's own generic
    defaults; `Credentials` left unserved - same constructed-type gap class as
    #2046).
  - **A-side (client) keys**: `SendReadProperty`, `SendWriteProperty`, and
    `SendSubscribeCOV` against a peer device (a separately-built local
    B-ACDC-CPP instance's Access Door 1 "Cobalt"), bound to interactive keys
    'd'/'w'/'r' and also fired once automatically at start-up.
- Objects: everything B-ACC-CPP has (base sensors, Access Door 1 "Cobalt",
  Credential Data Input 1 "Flax", Access Point 1 "Copper", Access Zone 1
  "Ebony", Access Credential 1 "Coral", Access Rights 1 "Cyan", Event Log 1
  "Beige", Schedule 1 "Saffron" / Calendar 1 "Cream", File 1 "Ivory",
  Notification Class 1 "Crimson", Network Port 1 "Vermilion") plus Access
  User 1 "Denim".

### Known gaps (see TODO.md; carried forward from B-ACC-CPP plus this
profile's own delta, each independently re-checked against this repo's own
pin rather than assumed stale)

- AE-AC-B alarm **generation** is not implementable through the customer API
  at this pin (carried forward unchanged).
  [chipkin/cas-bacnet-stack#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044)
- Several REQUIRED constructed-type access-family properties have no
  customer-facing Get callback, now also confirmed to include Access User's
  `Credentials` (`BACnetLIST of BACnetDeviceObjectReference`).
  [chipkin/cas-bacnet-stack#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046)
- `BACnetStack_AddEventLogObject` causes a continuous, non-fatal internal log
  flood from the first `Tick()` (carried forward).
  [chipkin/cas-bacnet-stack#2045](https://github.com/chipkin/cas-bacnet-stack/issues/2045)
- A live WriteProperty to Copper's `Access_Event` currently answers
  `unknown-object`; a live `AtomicReadFile` against Ivory during an active
  backup session aborted (both carried forward, neither root-caused).
- Cream's `Date_List` cannot be populated (inherited gap, stack issue #963).
- **DS-ACCDI-A stays unimplemented**, re-confirmed directly against this
  repo's own pinned stack source rather than assumed from the card: issue
  #492 was resolved at the stack's internal/test-tool level (per the stack's
  own CHANGELOG), but the actual add/configure Credential Data Input function
  (`BACnetStackTestTool_AddCredentialDataInputObject`) is still test-tool-only
  and not reachable from any customer-facing build. See TODO.md #7.
- The A-side `Send*` calls have no customer-facing callback to observe the
  peer's reply in-process (confirmed local accept-for-transmission only);
  verified on the wire independently instead. See TODO.md #8.

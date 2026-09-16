# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

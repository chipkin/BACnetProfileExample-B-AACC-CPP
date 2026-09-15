# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

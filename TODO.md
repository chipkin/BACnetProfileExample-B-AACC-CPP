# TODO — known gaps (all carried forward from B-ACC-CPP, sanity-checked against this repo's own
pin, plus items new to this profile's delta)

Stack pin: `abd4cee1c7f28ca8e1af4720849c4081082bbe82` (6.x @ 2026-09-10, reports 6.0.21) — the same
pin as B-ACC-CPP's seed, so items 1-6 below carry forward unchanged; each was re-checked against
this repo's own submodule checkout of that exact commit (not assumed), per the runbook's
instruction to independently sanity-check rather than blindly copy stale notes forward.

## 1. AE-AC-B: no customer-facing way to generate a true ACCESS_EVENT notification (carried forward)

Same gap as B-ACC-CPP's TODO.md #1, confirmed unchanged at this pin:
`BACnetStack_SetIntrinsicAccessEventAlgorithm` / `BACnetStack_SetAccessEventContext` are not on the
customer surface (`source/CASBACnetStackDLL.h` cites Sprint 75 / PR #169: moved to
`CASBACnetStackTestToolDLL`, ACCESS_EVENT is exercised from BTL, not a customer-facing host API).
No generic "send this event notification" export exists either. This file uses the same honest
substitute B-ACC-CPP does: Access Point 1 ("Copper")'s `Access_Event` property is real and
writable, armed with the generic `BACnetStack_SetIntrinsicChangeOfStateAlgorithmEnum` so a client
still gets a real notification for the property change — reported as `changeOfState(1)`, not
`accessEvent(9)`, disclosed here and in the README, not hidden.

**Filed:** [chipkin/cas-bacnet-stack#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044).

## 2. Access Credential / Access Rights / Access User: several REQUIRED constructed-type properties cannot be served (carried forward + extended)

Same class of gap as B-ACC-CPP's TODO.md #2: `Access_Credential,1.Authentication_Factors` and
`Access_Rights,1.Negative_Access_Rules` are `BACnetARRAY[N]` of a complex constructed type with no
dedicated typed Get callback on the customer surface, and no generic `GetPropertyConstructed`
export either (test-tool-only). The same applies to Access Point's `Access_Event_Time` /
`Access_Event_Credential`, and Access Zone's `Entry_Points`/`Exit_Points`.

**New to this profile's delta:** Access User 1 ("Denim")'s REQUIRED `Credentials` property
(`BACnetLIST of BACnetDeviceObjectReference`, cl. 12.32) hits the identical wall — grepped
`CASBACnetStackDLL.h` at this repo's own pin for any Get callback shaped for
`BACnetLIST of BACnetDeviceObjectReference`: zero hits. `Credentials` is therefore left unserved
here for the same reason Access Credential/Rights' constructed properties are, not a newly
discovered defect — just a new object instance of the same already-filed gap class. Denim's other
REQUIRED properties (`Object_Identifier`, `Object_Name`, `Object_Type`, `Status_Flags`,
`Reliability`, `User_Type`, `Global_Identifier`, `Property_List`) are all served correctly, either
by this file's own callbacks (`Object_Name`, `Global_Identifier` — the latter also WRITABLE) or by
the stack's own documented generic defaults (`property-profile-reference.md`: `User_Type`
"Generic Enumerated default: `0`", `Reliability` "Generic Enumerated default: `0`", the rest
"Computed by the stack").

**Filed:** [chipkin/cas-bacnet-stack#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046)
(also covers items 4 and 5 below, and now Access User's `Credentials`).

## 3. Event Log ("Beige"): `BACnetStack_AddEventLogObject` produces a continuous internal error log flood (carried forward)

Same gap as B-ACC-CPP's TODO.md #3 (bisection-verified there); this file adds Event Log 1 the same
way B-ACC-CPP does (`BACnetStack_AddEventLogObject`, AE-EL-I-B), so it is expected to reproduce
identically here. Re-verifying this specific repro live (not just carrying the note forward
unchecked) is part of this repo's own wire-verification pass — see the Verify section in
README.md for this session's result.

**Filed:** [chipkin/cas-bacnet-stack#2045](https://github.com/chipkin/cas-bacnet-stack/issues/2045).

## 4. Copper's `Access_Event` WriteProperty (the credential-read demo trigger) fails on the wire (carried forward)

Same gap as B-ACC-CPP's TODO.md #4. **Filed:** covered by
[chipkin/cas-bacnet-stack#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046).

## 5. File 1 ("Ivory") `File_Size` denies ReadProperty (carried forward)

Same gap as B-ACC-CPP's TODO.md #5. Not separately filed (root cause unconfirmed there); carried
forward as-is.

## 6. Calendar 1 ("Cream")'s `Date_List` — inherited, pre-existing gap (carried forward)

Same gap as B-ACC-CPP's TODO.md #6, against stack issue #963. This file uses the inline
`...WithCalendarEntry` exception form instead, exactly as B-ACC-CPP and B-AAC do.

## 7. DS-ACCDI-A: stays unimplemented — re-confirmed against the pinned stack source, not assumed stale

The profile card's own note says DS-ACCDI-A stays unchecked per stack issue #492, and the runbook
explicitly warned that several prior agents found cached notes like this stale — so this was
re-verified directly against `submodules/cas-bacnet-stack` at the pin rather than copied forward.
Two things are true at once here, and both were checked:

- The **stack's own internal changelog/spec-coverage docs** (`CHANGELOG.md` batch 104,
  `_spec/spec-coverage/bibbs.md`, `_spec/spec-coverage/00-index.md`) say issue #492 was
  **DELIVERED** (PR #550) and DS-ACCDI-A flipped `🟡` → `✅` — a stack-internal, test-tool-level
  resolution.
- The **actual customer-facing add/configure function is test-tool-only**, not on the surface this
  example (or any example in this series) links against. Grepped both DLL headers directly:
  `BACnetStackTestTool_AddCredentialDataInputObject` (plus
  `SetCredentialDataInputSupportedFormats`/`SetCredentialDataInputSupportedFormatClasses`/
  `PushCredentialDataInputFactor`) exist **only** in `source/CASBACnetStackTestToolDLL.h`; grepped
  `source/CASBACnetStackDLL.h` and `adapters/cpp/` for `CredentialDataInput`: no add/configure
  export on the customer surface at all (the one hit in `CASBACnetStackDLL.h` is an unrelated
  comment about `Supported_Formats` encoding). The Node adapter's own
  `AddCredentialDataInputObject` wrapper (`adapters/node/.../interface_objects.cc`) calls straight
  through to the test-tool function, confirming this isn't an adapter-generation gap either.

So **the card's note is still accurate for a customer-built application** (this example's own
Credential Data Input object 1 "Flax" — the profile's Table-K-9 requirement — is the generic
`BACnetStack_AddObject` + this file's own callbacks, same pattern as B-ACC-CPP's Flax and
B-ACCR-CPP's own copy source; the stack's *internal* CDI engine with real Present_Value/Update_Time
semantics per #492 is not reachable through any customer-facing add/configure call). DS-ACCDI-A
stays `☐` (not implemented) here, same as the card says — this is the same class of "engineering
fix landed, but only on the test-tool surface" pattern already established by item 1 (AE-AC-B /
#2044) and item 2 (#2046), not a new discovery, but it was independently re-confirmed rather than
assumed.

## 8. A-side (SendReadProperty/SendWriteProperty/SendSubscribeCOV): no customer-facing way to observe the peer's replies in-process

New to this profile's delta, not a functional break: grepped `CASBACnetStackDLL.h` for a
callback to receive a `ReadProperty-Ack`, a `WriteProperty` SimpleAck, or a COV notification this
device receives back after calling `SendReadProperty`/`SendWriteProperty`/`SendSubscribeCOV`:
zero hits (`RegisterCallbackReceived*Ack`, `*COVNotification*` — none exist; the only related,
and it's test-tool-only, hook is `BACnetStack_RegisterCallbackAuditNotificationReceived` per
`CASBACnetStackDLL.h`'s own PR #193 note). `BACnetProfileExample-B-OD-CPP` (this series' only
other SendReadProperty/SendWriteProperty user) does not register one either, for the same reason.
So this file's console can only confirm the local stack *accepted a Send* call for transmission*
(the bool return value), not that a reply arrived — the actual round trip is verified independently
on the wire with `bacpypes3`/`BAC0`, and by watching the peer B-ACDC-CPP instance's own console.
Not filed as a new stack issue: it is the same "customer surface stops at confirmed-service
send/serve, application-level consumption of the reply stream is not exposed" pattern already
established by items 1 and 7 above.

## 9. Live two-instance wire test results (this session)

Real second local B-ACDC-CPP instance (unmodified, device 389011, Access Door 1 "Cobalt", port
47809) run alongside this device (port 47808, `--peerPort 47809`), with `bacpypes3` as an
independent third observer against this device (port 47850):

- **SendReadProperty**: peer answered with a real ReadProperty-Ack (this device's own console:
  `RX 20 bytes from 127.0.0.1:47809`). Confirmed working.
- **SendWriteProperty**: the peer's own console logged
  `WriteProperty: Access Door 1 (Cobalt) <- unlock @ priority 8  (door is now unlock)` - the
  peer's door object genuinely changed state from this device's initiated write. Confirmed
  working.
- **SendSubscribeCOV**: accepted for transmission by this device's local stack and sent, but the
  peer's own console logged `Error: Services is not supported service=[5]` (service 5 =
  SubscribeCOV) and answered with an error rather than a subscription. Root cause confirmed, not
  a defect here: B-ACDC-CPP's own `README.md`/`main.cpp` state it "deliberately" does not
  implement SubscribeCOV/DS-COV-B at all. So DS-COV-A's request path is wire-verified as
  correctly formed and transmitted; a live, successful subscription against this specific peer
  object is not achievable, because the peer object the profile card specifies as the target does
  not support the service being tested against it. This is a test-setup mismatch inherent to the
  card's choice of peer/target, not a B-AACC-CPP or stack defect.
- **bacpypes3 (independent third-party client)** against this device directly: `Device,389010`
  `Object_Name`/`Vendor_Name`, `Access User 1 (Denim)` `Object_Name` = `"Denim"`,
  `Global_Identifier` (read `0`, then `WriteProperty <- 4242`, read back `4242`), `User_Type` =
  `asset` (the stack's own generic default, as expected - see TODO.md #2), `Reliability` =
  `no-fault-detected`, and `Access Door 1 (Cobalt)` `Object_Name` = `"Cobalt"` - all read back
  correctly.
- **Event Log flood (TODO.md #3 / #2045)**: reproduced identically in this repo's own build,
  confirming it is not specific to B-ACC-CPP's own binary.

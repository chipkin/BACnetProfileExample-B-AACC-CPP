# Tutorial - extending and reviewing the B-AACC example

[README.md](README.md) says what this example *is*. This document is the
*how*: how to extend it into your own device, who serves which property, how
to review the result for conformance, and what goes wrong when you get it
subtly right.

Read this once before you start changing `main.cpp`. The most expensive
mistake in this example is silent, and the section it lives in is
[Add a second instance of an object](#add-a-second-instance-of-an-object).

- [Extending the example](#extending-the-example)
- [What each object type needs you to serve](#what-each-object-type-needs-you-to-serve)
- [Who serves what: a worked example (Access Door 1 "Cobalt")](#who-serves-what-a-worked-example-access-door-1-cobalt)
- [Reviewing your device](#reviewing-your-device)
- [Troubleshooting](#troubleshooting)

## Extending the example

The example is intentionally linear so it's easy to change, even though it is
one of the larger repositories in the series.

**Change an object's value or name** - edit the constants / callbacks in
`main.cpp` (e.g. `g_analogInput1Value`, or the `"Cobalt"` string in
`GetPropertyCharString`).

**Change the device identity before you ship** - vendor ID, vendor name,
model name, description, firmware revision and device name are all in the
`CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`, with a
per-field note on each saying what to change it to. That block is the
authoritative checklist; it is in the source rather than here so it cannot be
skipped by someone who only reads the code.

**Change the A-side peer target** - `g_peerIp` / `g_peerPort` default to
`127.0.0.1:47809` and are overridable with `--peerIp` / `--peerPort`. If your
own peer device is not `BACnetProfileExample-B-ACDC-CPP`'s Access Door 1,
update `PEER_ACCESS_DOOR_INSTANCE` and the object identifier packed in
`SendReadPropertyToPeer()` / `SendWritePropertyToPeer()` /
`SendSubscribeCOVToPeer()` to match your real target.

### Add a second instance of an object

Read this whole recipe before starting - the last step is the one that is
easy to miss and the one BTL will fail you for.

> **Why skipping a step is SILENT, not loud.** Most of the `GetProperty*`
> callbacks in this file match on **both** object type *and* instance
> (`objectInstance == 1`), so a new instance falls through every one of them.
> `GetPropertyBool`'s `Out_Of_Service` branch is a partial exception: it
> matches on type alone for the base sensors and several access objects, so
> it answers a new instance for free - but most of this file's access-family
> properties (`Reliability`, `Global_Identifier`, `Credential_Status`, ...)
> are still matched on instance `1` explicitly and need a new branch.
>
> Falling through a callback does **not** reliably produce an error. The
> stack errors only for the few properties it refuses to invent (the same
> short list every example in this series documents: `Present_Value` on a
> non-commandable object, `Number_Of_States`, `Relinquish_Default` on an
> object that isn't commandable, `Local_Date`, `Local_Time`, and a Network
> Port's `APDU_Length`). For everything else it **silently substitutes a
> default**:
>
> | Property | If you forget to serve it | Loud? |
> |---|---|:--:|
> | `Object_Name` | reads back as the string **`"undefined"`** | **no** |
> | `Reliability` | reads back as **`no-fault-detected` (0)** by coincidence | **no** |
> | `Global_Identifier` | reads back as **`0`** | **no** |
> | `Out_Of_Service` | served on type alone for most objects here - works by accident | n/a |
>
> It is worse than "wrong value": the object's `Property_List` **still
> advertises the property**. So the object actively claims to have it, and
> then answers with a default. Nothing on the wire says you forgot anything -
> a half-added second Access Rights object still "scans OK" while reporting
> `Object_Name "undefined"`, which is a spec violation (duplicate/placeholder
> object names) and a hard BTL failure every scan tool will render as a
> perfectly good object.

```cpp
// 1) a new instance number, e.g. a second Access Rights object.
static const uint32_t ACCESS_RIGHTS_2_INSTANCE = 2;   // "Cyan 2"
static uint32_t g_rights2GlobalIdentifier = 0;
static bool g_rights2Enabled = true;

// 2) add the object (in main, next to the other BACnetStack_AddObject calls).
if (!BACnetStack_AddObject(g_deviceInstance, OBJECT_TYPE_ACCESS_RIGHTS, ACCESS_RIGHTS_2_INSTANCE)) {
    printf("Error: Failed to add Access Rights 2 (Cyan 2).\n");
    return 1;
}

// 3) serve its Object_Name, Global_Identifier, Reliability, Enable:
//    GetPropertyCharString:      AR/2 + Object_Name        -> "Cyan 2"
//    GetPropertyUnsignedInteger: AR/2 + Global_Identifier   -> g_rights2GlobalIdentifier
//    GetPropertyEnumerated:      AR/2 + Reliability         -> RELIABILITY_NO_FAULT_DETECTED
//    GetPropertyBool:            AR/2 + Enable              -> g_rights2Enabled

// 4) DO NOT SKIP: make Global_Identifier writable on the new instance too -
//    BACnetStack_SetPropertyWritable(g_deviceInstance, OBJECT_TYPE_ACCESS_RIGHTS,
//                                    ACCESS_RIGHTS_2_INSTANCE,
//                                    PROPERTY_IDENTIFIER_GLOBAL_IDENTIFIER, true);
//    The existing call in main() only covers instance 1. Skip this and
//    WriteProperty to instance 2 is rejected with "not writable" - a LOUD
//    failure, but one that is easy to attribute to the wrong cause if you
//    haven't read this far.
```

Then re-run the README's Verify steps **against the new instance**, not just
instance 1 - read every required property and **diff it against the existing
instance**. Any property that comes back `"undefined"` or `0` where the
original instance returns something real is a step you missed. Because the
failure is silent (see the table above), this diff is the only thing that
catches it.

## What each object type needs you to serve

The application must serve every REQUIRED property the stack does not
generate. It differs per type - this is the checklist for every object type
this example adds on top of the three base sensors (Analog/Binary/Multi-State
Input, unchanged from B-SS/B-ACC):

| Object type | You must serve | Plus |
|---|---|---|
| Access Door | `Object_Name`, `Reliability`, `Relinquish_Default`, door timing (`Door_Pulse_Time`, `Door_Extended_Pulse_Time`, `Door_Open_Too_Long_Time`) | `Present_Value` and `Priority_Array` are stack-resolved once the object is commandable; `Door_Status`/`Lock_Status`/`Secured_Status` (optional, enabled) |
| Credential Data Input | `Present_Value` (OctetString), `Object_Name`, `Supported_Formats`, `Update_Time`, `Reliability` | - |
| Access Point | `Object_Name`, `Reliability`, `Authentication_Status`, `Active_Authentication_Policy`, `Number_Of_Authentication_Policies`, `Authorization_Mode`, `Access_Event`, `Access_Event_Tag` | `Access_Event_Time`/`Access_Event_Credential` are unservable - see TODO.md #2 |
| Access Zone | `Object_Name`, `Occupancy_State`, `Reliability`, `Global_Identifier` | `Entry_Points`/`Exit_Points` are unservable - see TODO.md #2 |
| Access Credential | `Object_Name`, `Global_Identifier`, `Reliability`, `Credential_Status`, `Reason_For_Disable`, `Credential_Disable` | `Authentication_Factors`/`Activation_Time`/`Expiration_Time`/`Assigned_Access_Rights` are unservable - see TODO.md #2 |
| Access Rights | `Object_Name`, `Global_Identifier`, `Reliability`, `Enable` | `Negative_Access_Rules`/`Positive_Access_Rules` are unservable - see TODO.md #2 |
| **Access User** *(new in this profile)* | `Object_Name`, `Global_Identifier` | `Reliability`/`User_Type` left to the stack's generic default (both happen to be correct by coincidence); `Credentials` is unservable - see TODO.md #2 |
| Event Log | `Object_Name` | Everything else is stack-generated or stack-held; adding this object triggers a verified internal log flood - see TODO.md #3 |
| Schedule | `Object_Name`, `Reliability`, `Out_Of_Service` | The Schedule-owned properties (`Present_Value`, `Weekly_Schedule`, `Schedule_Default`, ...) are genuinely populated by `BACnetStack_AddScheduleObject`/`AddScheduleWeeklyTimeValue`/`SetScheduleDefault` at start-up, not a `GetProperty*` callback |
| Calendar | `Object_Name`, `Present_Value` | `Date_List` cannot be populated through the customer API - see TODO.md #6 |
| File | `Object_Name`, `File_Type`, `File_Size`, `Modification_Date`, `Archive`, `Read_Only` | `File_Access_Method` is stack-generated |
| Notification Class | `Object_Name` | Everything else is genuinely populated by `BACnetStack_AddNotificationClassObject`/`AddRecipientToNotificationClass` at start-up |
| Network Port | `Object_Name`, `Out_Of_Service`, `Network_Type`, `Protocol_Level`, `Changes_Pending` | Required on every device |

## Who serves what: a worked example (Access Door 1 "Cobalt")

The single most common question when reading this file is "who answers this
property?" Cobalt is the most instructive object because it is
**commandable** (the profile's DS-ACUC-B "unlock command" BIBB) and also
this device's A-side peer's namesake object:

| Property | Served by | How |
|---|---|---|
| `Object_Identifier` | **stack** | generated from the object you added |
| `Object_Type` | **stack** | generated |
| `Property_List` | **stack** | generated |
| `Status_Flags` | **stack** | generated |
| `Event_State` | **stack**, sort of | no intrinsic alarming here, so it reads `normal` only because `normal` is the enumeration's zero value - correct by coincidence, not design |
| `Reliability` | **you** | `GetPropertyEnumerated`, matched on the whole access-object-type group |
| `Out_Of_Service` | **you** | `GetPropertyBool`, matched on type only |
| `Present_Value` | **stack** | the object is commandable (`SetPropertyWritable` on `Present_Value`); the stack resolves the effective value from the 16-slot `Priority_Array` your `GetPropertyBool`/`GetPropertyEnumerated` callbacks expose per slot |
| `Priority_Array` | **stack**, fed by **you** | the stack assembles the array; you answer each slot (`GetPropertyBool` for whether it's set, `GetPropertyEnumerated` for its value) via `ReadDoorPrioritySlot()` |
| `Relinquish_Default` | **you** | `GetPropertyEnumerated` |
| `Door_Status` / `Lock_Status` / `Secured_Status` *(optional, enabled)* | **you** | `GetPropertyEnumerated`, derived from whichever priority slot is currently effective |
| `Door_Pulse_Time` / `Door_Extended_Pulse_Time` / `Door_Open_Too_Long_Time` | **you** | `GetPropertyUnsignedInteger`, fixed demo constants |

Every object, not just this one, is in [docs/PICS.md](docs/PICS.md).

The A-side (client) keys don't serve properties at all - they **initiate**
requests. `SendReadPropertyToPeer()` / `SendWritePropertyToPeer()` /
`SendSubscribeCOVToPeer()` pack a peer object identifier and call
`BACnetStack_SendReadProperty` / `SendWriteProperty` / `SendSubscribeCOV`
directly; there is no `GetProperty*` callback involved on the initiating
side, because this device is not answering a request there, it is making
one. See TODO.md #8 for why this file's own console cannot show you the
peer's actual reply.

## Reviewing your device

After you have changed anything, review it against the conformance statement
rather than against "it looked fine in the explorer":

1. Regenerate [docs/PICS.md](docs/PICS.md) after editing `docs/objects.json`
   (see [Keeping the PICS honest](#keeping-the-pics-honest) below). A ⚠ row
   is a required property nothing serves.
2. Read **every** property listed for **every** object with a BACnet client,
   and compare the value against the PICS. `"undefined"` and `0` are two of
   the shapes a missed callback takes; an `Abort(other)` or
   `Error(unknown-property)` on a constructed-type property (see the table
   above) is *expected* for the properties TODO.md documents as unservable -
   confirm it's one of those, not a new one.
3. Diff a new object of a type against the existing one of that type.
   Anything that differs and shouldn't is a callback that matched on
   instance.
4. Confirm DS-ACUC-B: WriteProperty Cobalt's `Present_Value` to `unlock`(1)
   at a priority; confirm `Lock_Status`/`Door_Status` follow; relinquish and
   confirm it falls back to `Relinquish_Default`.
5. Confirm the A-side keys ('d'/'w'/'r') are accepted for transmission by
   this device's own console, and independently confirm the peer actually
   received them by watching the **peer's** console (see TODO.md #8 - this
   device cannot show you the peer's reply itself).
6. Confirm the services this profile does **not** implement stay rejected or
   documented as gaps: DS-ACCDI-A (there is no object to test against - see
   TODO.md #7) and a true AE-AC-B `accessEvent`-typed notification (Copper's
   `Access_Event` is writable and readable, but no intrinsic algorithm
   watches it - see TODO.md #1).

### Keeping the PICS honest

`docs/PICS.md` is partly generated. `docs/objects.json` describes each
object and who serves which property; the series tool regenerates the object
tables from it plus the stack's own `docs/property-profile-reference.md` at
the pinned commit:

```bash
python tools/gen-objects-properties.py BACnetProfileExample-B-AACC-CPP            # rewrite
python tools/gen-objects-properties.py BACnetProfileExample-B-AACC-CPP --check    # fail if stale
```

(That tool lives in the example-series repository, not in this one. If you
only have this repository, edit the generated block by hand and keep it
matching the callbacks in `main.cpp`.)

When you add an object or a property to `main.cpp`, update
`docs/objects.json` in the same change and regenerate. The `app` list is what
the callbacks serve; `accepted` is for a required property you deliberately
leave to the stack's default, and each one needs a justification in
`docs/objects.json`'s `note` field and/or `TODO.md`. Anything required, not
in `app` and not in `accepted`, comes out as a ⚠ row - that is a defect, not
a feature. As of this restructure, `docs/objects.json` also carries the
Device object (previously omitted from the generated tables); its `stack` /
`accepted` split documents which device-wide facts the stack alone knows
versus which stack-configured defaults this example deliberately does not
override.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected for the benign sources every example in this series shares** - the device hears its own broadcast I-Am, and a one-time BACnet/SC UUID notice. **Also expected and specific to this repository:** a **continuous** (not one-time) `BACnetDateTime::operator=() ... Failed to set the date/time` flood starting from the very first `Tick()`, caused by adding the Event Log object (Beige) - reproduced and bisection-verified in this repo's own build. It is currently believed non-fatal (the device keeps answering requests correctly) but was not exhaustively characterised. See TODO.md #3 / [cas-bacnet-stack#2045](https://github.com/chipkin/cas-bacnet-stack/issues/2045). |
| ReadProperty of `Access_Event_Time`, `Access_Event_Credential`, `Entry_Points`, `Exit_Points`, `Authentication_Factors`, `Activation_Time`, `Expiration_Time`, `Assigned_Access_Rights`, `Negative_Access_Rules`, `Positive_Access_Rules`, or Access User's `Credentials` returns `Abort(other)` or `Error(unknown-property)` | **Expected - a verified stack gap, not a bug in this example.** These are all `BACnetARRAY`/`BACnetLIST` of a complex constructed type with no customer-facing typed Get callback and no generic constructed-property export either. See TODO.md #2 / [cas-bacnet-stack#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046). |
| WriteProperty to Copper's `Access_Event` returns `Error(unknown-object)` | **Expected - a verified, not-yet-root-caused stack gap.** See TODO.md #4. |
| `AtomicReadFile` against Ivory aborts during an active backup session | **Expected - a verified, not-yet-root-caused stack gap.** See TODO.md #5. |
| Cream's `Date_List` cannot be populated | **Expected - an inherited gap against stack issue #963**, same as B-AAC/B-ACC. Saffron's one exception uses the inline calendar-Date form instead of a Cream reference, so scheduling still works. See TODO.md #6. |
| No true `accessEvent`(9)-typed event notification is ever produced, even though Copper's `Access_Event` changes and a notification does arrive | **Expected - see TODO.md #1.** The notification you do see is real (generated by the stack's generic `changeOfState` intrinsic algorithm), but its BACnet Event Type is `changeOfState`(1), not `accessEvent`(9), because the access-specific intrinsic algorithm is test-tool-only at this pin. |
| The 'd'/'w'/'r' A-side keys print "sent" but you can't tell if the peer answered | **Expected - see TODO.md #8.** This device's console can only confirm the local stack accepted the `Send*` call for transmission, not that a reply arrived. Watch the **peer's** own console, or use an independent third-party client (`bacpypes3`/`BAC0`) to observe the wire directly. |
| SendSubscribeCOV to the peer's Access Door fails with `Error: Services is not supported service=[5]` on the peer | **Expected if your peer is an unmodified `BACnetProfileExample-B-ACDC-CPP`** - it deliberately does not implement SubscribeCOV. The request path from this device is still correctly formed and sent; this is a property of the peer you chose, not a defect here. |
| CMake error: *"CAS BACnet Stack adapter not found under: ..."* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~600 stack files. Only the first build is slow. |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808 (including your own peer instance, if you forgot `--port`/`--peerPort`). Stop it, or run with `--port <n>`. |
| Client sends Who-Is but sees no I-Am | Firewall is blocking the UDP port, or the client and device are on different subnets (Who-Is is a broadcast). Allow the port; test on the same subnet first. |

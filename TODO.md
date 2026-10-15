# TODO - known gaps

Stack Pin: `6.x` @ `64b2cfac5` (6.0.23). Every entry was re-checked at this pin
on 2026-10-15, on the wire where it can be observed.

**This is a Blocked Example.** The B-AACC Profile Function (ANSI/ASHRAE
135-2024 L.6.1: "performs physical access control authentication and
authorization for physical access. It supports the modification of its Access
User, Access Credential, and Access Rights objects by another device ... It is
capable to use remote Access Control Door Controller devices and remote Access
Control Credential Reader devices", with access-event notifications) needs
items 1 and 2, and both are stack gaps the owner ruled on 2026-10-15 are not
promoted to the customer interface for now (stack PR #3937, commit
`aeaa1a37e`). Items 5 and 6 are the A-side half; they would be needed too.

## 1. AE-AC-B: no customer-facing way to generate an ACCESS_EVENT notification

**Stack issue:** [chipkin/cas-bacnet-stack#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) (open; not promoted).

Same as B-ACC-CPP's TODO.md #1. At the pin the intrinsic access-event algorithm
(`BACnetStackTestTool_SetIntrinsicAccessEventAlgorithm`,
`BACnetStackTestTool_SetAccessEventContext`) is declared only in
`CASBACnetStackTestToolDLL.h`, there is no generic "send this event
notification" export, and the stack rejects the generic change-of-state
algorithm on an Access Point ("intrinsic algorithm changeOfState is not
supported by objectType=[33]"). So nothing in this example generates an event
notification of any kind. Earlier versions of this file and the README said a
`changeOfState` notification was produced as a substitute; it was not.

Knock-on: AE-EL-I-B (K.2.21, required for B-AACC) is not claimed either. Event
Log 1 ("Beige") exists, but with no notification generated it never collects
anything.

## 2. DS-ACUC-B / DS-ACSC-B: the authorization-data properties cannot be served

**Stack issue:** [chipkin/cas-bacnet-stack#2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150) (open; not promoted; part A of [#2046](https://github.com/chipkin/cas-bacnet-stack/issues/2046)).

The discovery Wire Test reads every property in every object's
`Property_List`. At this pin six required properties do not read as a value
(Windows and Linux, the same answers):

| Object | Property | Answer |
|---|---|---|
| Access Credential 1 "Coral" | `Assigned_Access_Rights` (256) | Error property / unknown-property |
| Access Credential 1 "Coral" | `Authentication_Factors` (257) | Error property / unknown-property |
| Access Point 1 "Copper" | `Access_Doors` (246) | Error property / unknown-property |
| Access Point 1 "Copper" | `Access_Event_Credential` (249) | Abort, reason other |
| Access Rights 1 "Cyan" | `Negative_Access_Rules` (288) | Error property / unknown-property |
| Access Rights 1 "Cyan" | `Positive_Access_Rules` (302) | Error property / unknown-property |

They say which credential carries which factors and rights, and which rules
allow whom through which point. Without them another device cannot read or
configure the authorization data, which is the Profile Function and the
substance of DS-ACUC-B (K.1.34) and DS-ACSC-B (K.1.36). The Wire Test reports
each as a `[KNOWN GAP]`; when one starts reading as a value it prints
`[GAP CLOSED]`.

Same class, not named in #2150: Access User 1 ("Denim")'s required
`Credentials` (265, BACnetLIST of BACnetDeviceObjectReference) reads as an
empty list and cannot be filled through the customer interface. #2150's
proposed "List of DOR" callback would cover it.

## 3. Calendar 1 ("Cream") still uses the generic object

Not a stack gap any more: stack #963 is closed, and the stack's Calendar engine
is on the customer interface at this pin (`BACnetStack_AddCalendarObject`,
`AddCalendarDateEntry`, `AddScheduleExceptionEventWithCalendarReference`). This
example still adds Cream with `BACnetStack_AddObject` and serves
`Present_Value` = false itself, and Saffron uses an inline exception date.
Moving Cream to the engine is example work for the Profile-functional rework.

## 4. Backup/restore payload round-trip not re-tested

At 6.0.21 an `AtomicReadFile` against File 1 ("Ivory") during an active backup
session aborted (B-ACC-CPP). Stack #2152 (closed) covered it with the
`File_Size` defect; `File_Size` now reads as a value. The full backup and
restore cycle has not been re-run at this pin.

## 5. DS-ACCDI-A: not claimed

K.1.39 requires subscribing for COV in a remote Credential Data Input and
receiving "all forms of BACnetAuthenticationFactor values conveyed in COV
notifications". This example sends no such subscription, and has no customer
callback to receive COV notifications anyway (item 6). Stack #492 (closed)
delivered the stack's own Credential Data Input engine, but its add/configure
exports (`BACnetStackTestTool_AddCredentialDataInputObject` and friends) are
still test-tool only at this pin (`CASBACnetStackDLL.h` names Credential Data
Input only in a `Supported_Formats` comment). That engine is the B side; for
this A-side BIBB the missing piece is item 6.

## 6. A-side: no customer-facing way to consume the peer's replies

`SendReadProperty`, `SendWriteProperty` and `SendSubscribeCOV` are customer
exports and this example calls them (keys `d`, `w`, `r`, and once at start-up).
The customer header has no callback that delivers a ReadProperty-Ack, a
WriteProperty SimpleACK or a COV notification the device receives back, so the
example cannot use what it reads - and "retrieve the values of BACnet objects
from other devices" in L.6.1 means using them. A workaround through
`BACnetStack_RegisterCallbackReceiveMessageForPort` (decoding the raw APDU in
the application) has not been tried. No stack issue is filed for this; it is a
question for the Profile-functional rework.

At v1.0.0 (stack 6.0.21) a two-instance run against an unmodified B-ACDC-CPP
peer (device 389011 "Chipkin Example B-ACDC", port 47809) showed:
SendReadProperty answered with a ReadProperty-Ack (seen as an RX line);
SendWriteProperty changed the peer's door (peer console:
`WriteProperty: Access Door 1 (Cobalt) <- unlock @ priority 8`);
SendSubscribeCOV refused by the peer (`Services is not supported service=[5]`),
because B-ACDC does not implement SubscribeCOV. So DS-COV-A has never succeeded
against a real peer. That run has not been repeated at this pin.

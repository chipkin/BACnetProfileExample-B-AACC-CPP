# Plan (STUB): B-AACC (Advanced Access Control Controller) — C++ example

> **STATUS: STUB.** Seed facts below. Expand from
> [`bacnet-profile-plan-template.md`](../../bacnet-profile-plan-template.md) after the
> sample plans ([B-LD](../../BACnetProfileExample-B-LD-CPP/docs/plan.md),
> [B-BC](../../BACnetProfileExample-B-BC-CPP/docs/plan.md)) are reviewed.

**Profile:** B-AACC · **Family:** Annex L.6 (Access Control Controller) · **Role:** B
(with A-side advertise) · **Archetype:** Controller · **Difficulty:** 5/5 ·
**Build wave:** 4 (builds on B-ACC)

**Thesis:** B-ACC **plus** a fuller access object set and a few A-side advertise
BIBBs. Small delta over B-ACC.

## Required BIBBs (profiles.md L.6)
B-ACC's set **+ DS-COV-A, DS-ACAD-A, DS-ACCDI-A** (A-side advertise).

## Services to enable
- All of B-ACC's services + minimal A-side initiate (`Send*`, B-OD pattern).

## Objects (baseline + B-ACC objects + )
- Access User 1 (the fuller family); otherwise the B-ACC object set.

## Shared features
- **DEFINE:** none.
- **REUSE:** everything from B-ACC. Delta = more access objects + minor A-side
  advertise.

## Known stack gaps
- Same as B-ACC (schedule engine, recipient-by-address, backup/restore) **+** the
  A-side-initiate-footprint note (master plan §7 risk; B-BC §6.5). profiles.md: ✅
  S75.

## Notes / open questions
- Build **immediately after B-ACC**. Decide the minimal `Send*` set so it honestly
  shows DS-*-A without becoming a workstation (same judgement call as B-BC).

# Plan: B-AACC (Advanced Access Control Controller) — C++ example

> **STATUS: IMPLEMENTED.** This plan-only stub has been superseded by the actual
> implementation. See:
> - [`main.cpp`](../main.cpp) — the example itself, with the full design rationale and
>   every verified stack limitation in its file header.
> - [`README.md`](../README.md) — profile overview, BIBB table, object table, A-side
>   client keys, build/verify instructions.
> - [`TODO.md`](../TODO.md) — every known gap, verified against the pinned stack
>   source and/or the wire, with filed `chipkin/cas-bacnet-stack` issues.
> - [`docs/objects.json`](objects.json) — source for the generated "Objects and
>   properties" reference table in README.md.

Seeded from [BACnetProfileExample-B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP)
(Wave 3, released v1.0.0) per the series runbook's Procedure B pattern, extending it with an
Access User object and the A-side (client) `SendReadProperty`/`SendWriteProperty`/
`SendSubscribeCOV` keys.

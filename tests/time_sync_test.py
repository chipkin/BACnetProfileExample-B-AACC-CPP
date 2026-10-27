#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-AACC Wire Test - a workstation sets the controller's clock (DM-TS-B, DM-UTC-B).

    python3 tests/time_sync_test.py [--exe build/BACnetExampleBAACC] [--port 47830]

The workstation moves the controller's clock with TimeSynchronization (cl. 16.7) and
UTCTimeSynchronization (cl. 16.8) and reads the Device's Local_Date and Local_Time back.
Python 3 standard library only.

  1. Control: before any sync, Local_Date is today's date on this host.
  2. TimeSynchronization 2026-12-25 10:00 -> Local_Date 2026-12-25, Local_Time about 10:00.
  3. UTCTimeSynchronization Monday 2026-10-19 07:00 (UTC_Offset 0) -> Local_Date 2026-10-19,
     Local_Time about 07:00.

Exit code 0 = every check passed.
"""
import argparse
import datetime
import sys
import time
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

import wiretest  # noqa: E402  (the vendored harness at the repository root)
from wiretest import Workstation, record, summary  # noqa: E402
from wiretest import alarm as alarm_codec  # noqa: E402

DEVICE = (wiretest.OBJECT_TYPE_DEVICE, 389010)
PROPERTY_LOCAL_TIME = 57
SERVICE_UTC_TIME_SYNCHRONIZATION = 9
SETTLE = 1.0                        # seconds for the controller to apply the sync
TIME_TOLERANCE_SECONDS = 30


def parser():
    arguments = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("--exe", default=str(wiretest.default_exe(REPOSITORY, "BACnetExampleBAACC")),
                           help="path to BACnetExampleBAACC (default: build/BACnetExampleBAACC)")
    arguments.add_argument("--port", type=int, default=47830,
                           help="the advanced access control controller's UDP port (default 47830)")
    return arguments


def synchronize(workstation, port, moment, utc=False):
    apdu = alarm_codec.time_synchronization(moment.year, moment.month, moment.day, moment.isoweekday(),
                                            moment.hour, moment.minute, moment.second)
    if utc:
        apdu = apdu[:1] + bytes([SERVICE_UTC_TIME_SYNCHRONIZATION]) + apdu[2:]
    workstation.send_unconfirmed(apdu, port)
    time.sleep(SETTLE)


def local_date(workstation, port):
    """Device Local_Date as a datetime.date, or None."""
    octets = workstation.read_property(port, *DEVICE, alarm_codec.PROPERTY_LOCAL_DATE).value_octets
    if octets is None or len(octets) != 5:
        return None
    return datetime.date(1900 + octets[1], octets[2], octets[3])


def local_time_seconds(workstation, port):
    """Device Local_Time as seconds after midnight, or None."""
    octets = workstation.read_property(port, *DEVICE, PROPERTY_LOCAL_TIME).value_octets
    if octets is None or len(octets) != 5:
        return None
    return octets[1] * 3600 + octets[2] * 60 + octets[3]


def near(seconds, moment):
    target = moment.hour * 3600 + moment.minute * 60 + moment.second
    return seconds is not None and abs(seconds - target) <= TIME_TOLERANCE_SECONDS


def main():
    args = parser().parse_args()
    controller = wiretest.start(args.exe, ["--port", args.port], "B-AACC")
    workstation = Workstation()
    try:
        before = local_date(workstation, args.port)
        today = datetime.date.today()
        record("Control: before any sync, Local_Date is this host's date",
               before in (today, today - datetime.timedelta(days=1), today + datetime.timedelta(days=1)),
               f"read {before}, host {today}")

        christmas = datetime.datetime(2026, 12, 25, 10, 0, 0)
        synchronize(workstation, args.port, christmas)
        synced = local_date(workstation, args.port)
        record("TimeSynchronization 2026-12-25 10:00: Local_Date reads 2026-12-25", synced == christmas.date(),
               f"read {synced}")
        seconds = local_time_seconds(workstation, args.port)
        record("TimeSynchronization 2026-12-25 10:00: Local_Time reads about 10:00", near(seconds, christmas),
               f"read {seconds} s after midnight")

        monday_seven = datetime.datetime(2026, 10, 19, 7, 0, 0)
        synchronize(workstation, args.port, monday_seven, utc=True)
        synced = local_date(workstation, args.port)
        record("UTCTimeSynchronization 2026-10-19 07:00 (UTC_Offset 0): Local_Date reads 2026-10-19",
               synced == monday_seven.date(), f"read {synced}")
        seconds = local_time_seconds(workstation, args.port)
        record("UTCTimeSynchronization 2026-10-19 07:00 (UTC_Offset 0): Local_Time reads about 07:00",
               near(seconds, monday_seven), f"read {seconds} s after midnight")
    finally:
        workstation.close()
        controller.stop()
    return summary()


if __name__ == "__main__":
    sys.exit(main())

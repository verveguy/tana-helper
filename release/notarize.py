"""[macOS] Automatic notarization process.

Usage: python notarize FILE [NOTARIZATION_UUID]

If NOTARIZATION_UUID is given, then the noratization process will continue.
Else a new notarization process will be started
"""

import json
import os
import re
import subprocess
import sys
from typing import List, Pattern, Tuple

BUNDLE_IDENTIFIER = os.getenv("BUNDLE_IDENTIFIER")
NOTARIZATION_USERNAME = os.getenv("NOTARIZATION_USERNAME")
NOTARIZATION_PASSWORD = os.getenv("NOTARIZATION_PASSWORD")
NOTARIZATION_TEAMID = os.getenv("NOTARIZATION_TEAMID")

def submit_dmg_for_notarization(file: str) -> str:
    """Upload the *file* and wait for its notarization UUID.

    The command will return something like:

        Conducting pre-submission checks for nuxeo-drive-x.x.x.dmg and initiating
        connection to the Apple notary service...
        Submission ID received
        id: hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh
        Successfully uploaded file
        id: hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh
        path: /Users/runner/work/nuxeo-drive/nuxeo-drive/dist/nuxeo-drive-x.x.x.dmg
        Waiting for processing to complete.

        Current status: In Progress...
        Current status: In Progress....
        Current status: In Progress.....
        Current status: In Progress......
        Current status: In Progress.......
        Current status: In Progress........
        Current status: In Progress.........
        Current status: In Progress..........
        Current status: In Progress...........
        Current status: In Progress............
        Current status: In Progress.............
        Current status: In Progress..............
        Current status: In Progress...............
        Current status: In Progress................
        Current status: In Progress.................
        Current status: Accepted..................Processing complete
        id: hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh
        status: Accepted

    And we are interested in the value of id and status.
    """
    print(f">>> [notarization] Uploading {file!r}", flush=True)
    print("    (it may take a while)", flush=True)

    cmd = [
        "xcrun",
        "notarytool",
        "submit",
        file,
        "--apple-id",
        NOTARIZATION_USERNAME,
        "--password",
        NOTARIZATION_PASSWORD,
        "--team-id",
        NOTARIZATION_TEAMID,
        "--wait",
    ]

    output = call(cmd)
    print(f">>> [notarization] {output}")
    uuid = get_notarization_id(output)
    status = get_notarization_status(output)
    return (uuid if uuid else "", status if status else "")


def fetch_notarization_logs(uuid: str) -> Tuple[bool, str]:
    """Poll at regular interval for the final notarization status of the given *uuid*.

    The command will return something like:

        Successfully downloaded submission log
        id: 5ff518fe-1581-418d-9c9b-b14ac8df3197
        location: /Users/runner/work/nuxeo-drive/nuxeo-drive/notarization_report.json

    """
    print(">>> [notarization] Waiting for notarization logs path..", flush=True)

    cmd = [
        "xcrun",
        "notarytool",
        "log",
        uuid,
        "--apple-id",
        NOTARIZATION_USERNAME,
        "--password",
        NOTARIZATION_PASSWORD,
        "--team-id",
        NOTARIZATION_TEAMID,
        "notarization_report.json",
    ]

    output = call(cmd)
    location = get_notarization_report(output)
    print(f">>> [notarization] {output}")

    return location


def get_notarization_report(
    output: str, pattern: Pattern = re.compile(r"location: (.+)")
) -> str:
    """Get the notarization report location/path from a given *output*."""
    return re.findall(pattern, output)[0]


def get_notarization_status(
    output: str, pattern: Pattern = re.compile(r"status: (.+)")
) -> str:
    """Get the notarization status from a given *output*."""
    return re.findall(pattern, output)[-1]


def get_notarization_id(output: str, pattern: Pattern = re.compile(r"id: (.+)")) -> str:
    """Get the notarization id from a given *output*."""
    return re.findall(pattern, output)[0]


def staple_the_notarization(file: str) -> None:
    """Staple the notarization to the *file*."""
    call(["xcrun", "stapler", "staple", "-v", file])
    print(">>> [notarization] Done with success ᕦ(ò_óˇ)ᕤ", flush=True)


def call(cmd: List[str]) -> str:
    """Make a system call and retrieve its output from stdout and stderr."""
    exitcode, output = subprocess.getstatusoutput(" ".join(cmd))
    if exitcode != 0:
        print(" !! ERROR", flush=True)
        print(output, flush=True)
        raise subprocess.CalledProcessError(exitcode, cmd)
    return output


def display_notarization_logs(notary_logs_path: str) -> str:
    """Print notarization report."""
    print(f">>> Report loading from {notary_logs_path}", flush=True)

    with open(file=notary_logs_path, mode="r") as log_file:
        data = json.load(log_file)
        formated_logs = json.dumps(data, indent=4)
        print(formated_logs, flush=True)


def main(file: str, uuid: str = "") -> int:
    """Entry point."""

    status = "Accepted"
    if not uuid:
        # This is a new DMG file to notarize
        uuid, status = submit_dmg_for_notarization(file)
    if not uuid:
        print(" !! No notarization UUID found.", flush=True)
        return 1

    if not status or status != "Accepted":
        print(" !! Notarization failed. Check the report for details.", flush=True)
        return 2

    notary_logs_path = fetch_notarization_logs(uuid)

    if not notary_logs_path:
        print(" !! Notarization logs path not found.", flush=True)
        return 3

    # Below method will display notarization logs (Useful in case issue occurs during notarization)
    # display_notarization_logs(notary_logs_path)

    staple_the_notarization(file)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
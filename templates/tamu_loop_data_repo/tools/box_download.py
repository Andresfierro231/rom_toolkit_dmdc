#!/usr/bin/env python3
"""Download a file from Box by file ID using a bearer token."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_id")
    parser.add_argument("output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get("BOX_ACCESS_TOKEN")
    if not token:
        print("Missing BOX_ACCESS_TOKEN environment variable.", file=sys.stderr)
        return 2

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://api.box.com/2.0/files/{args.file_id}/content"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request) as response, out.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    except urllib.error.HTTPError as exc:
        print(f"Box download failed: HTTP {exc.code}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Box download failed: {exc.reason}", file=sys.stderr)
        return 1

    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

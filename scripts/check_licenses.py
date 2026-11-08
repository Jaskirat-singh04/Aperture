"""Fail if any installed dependency is GPL or AGPL licensed.

LGPL is not flagged on purpose, see docs/adr/0004-psycopg-lgpl-dependency.md
for why psycopg (LGPL-3.0, with a linking exception) is an accepted
exception to the "permissive licenses only" rule, GPL and AGPL are not.

Run with: uv run python scripts/check_licenses.py
(after `uv sync`, this reads the licenses of packages installed in the
current environment)
"""

import json
import subprocess
import sys


def is_disallowed(license_name: str) -> bool:
    """True for GPL or AGPL (abbreviated or spelled out), false for LGPL.

    License strings vary a lot between packages ("GPL-3.0", "GNU General
    Public License v3 (GPLv3)", "GNU Affero General Public License v3", ...),
    so this checks for the distinguishing words rather than one fixed
    pattern.
    """

    upper = license_name.upper()
    if "AFFERO" in upper or "AGPL" in upper:
        return True
    if "LGPL" in upper or "LESSER" in upper:
        return False
    return "GPL" in upper or "GENERAL PUBLIC LICENSE" in upper


def main() -> int:
    result = subprocess.run(
        ["uv", "run", "pip-licenses", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    packages = json.loads(result.stdout)

    violations = [pkg for pkg in packages if is_disallowed(pkg.get("License", ""))]

    if violations:
        print("Disallowed (GPL/AGPL) licenses found:", file=sys.stderr)
        for pkg in violations:
            print(f"  {pkg['Name']} {pkg['Version']}: {pkg['License']}", file=sys.stderr)
        return 1

    print(f"Checked {len(packages)} packages, no GPL or AGPL licenses found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

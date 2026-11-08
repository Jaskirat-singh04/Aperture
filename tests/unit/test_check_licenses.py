"""Unit tests for the GPL/AGPL license detection used in CI."""

import pytest

from scripts.check_licenses import is_disallowed


@pytest.mark.parametrize(
    ("license_name", "expected"),
    [
        ("LGPL-3.0-only", False),
        ("GNU Library or Lesser General Public License (LGPL)", False),
        ("GNU General Public License v3 (GPLv3)", True),
        ("GNU General Public License v2 or later (GPLv2+)", True),
        ("GNU Affero General Public License v3", True),
        ("AGPL-3.0", True),
        ("MIT License", False),
        ("Apache Software License", False),
        ("BSD License", False),
        ("Mozilla Public License 2.0 (MPL 2.0)", False),
    ],
)
def test_is_disallowed(license_name: str, expected: bool) -> None:
    assert is_disallowed(license_name) is expected

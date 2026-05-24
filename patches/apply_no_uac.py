#!/usr/bin/env python3
"""
Apply no-UAC (current-user install) modifications to darktable's Inno Setup template.

This script modifies packaging/windows/darktable.iss.in to:
  1. Enable per-user installation (PrivilegesRequired=lowest)
  2. Remove the option for the user to switch to admin mode during setup
     (remove PrivilegesRequiredOverridesAllowed) so this build is strictly
     current-user-only
  3. Append "-no-uac" to the installer output filename so it is clearly
     distinguishable from the official machine-wide installer

The script exits with a non-zero status if any critical modification fails,
so the CI pipeline aborts rather than accidentally shipping a UAC-triggering
installer.

Usage:
    python apply_no_uac.py <path/to/darktable.iss.in>
"""

import os
import re
import sys


def apply_no_uac_patch(iss_in_path: str) -> None:
    """Modify the Inno Setup template for per-user (no-UAC) installation."""

    if not os.path.exists(iss_in_path):
        print(f"ERROR: file not found: {iss_in_path}", file=sys.stderr)
        sys.exit(1)

    with open(iss_in_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    original = content
    changes: list[str] = []

    # ------------------------------------------------------------------
    # 1. Ensure PrivilegesRequired=lowest
    #
    # The upstream template ships with the line commented out:
    #   ; PrivilegesRequired=lowest
    #
    # We uncomment it.  If an explicit (uncommented) PrivilegesRequired
    # is already present with a different value we overwrite it.
    # If no form of the directive exists we insert one after [Setup].
    # ------------------------------------------------------------------
    commented_pattern = re.compile(
        r"^;+\s*(PrivilegesRequired\s*=\s*lowest\s*)$",
        re.MULTILINE | re.IGNORECASE,
    )
    explicit_pattern = re.compile(
        r"^(PrivilegesRequired\s*=\s*)(\S+)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    if commented_pattern.search(content):
        content = commented_pattern.sub(r"\1", content)
        changes.append("Uncommented PrivilegesRequired=lowest")
    elif m := explicit_pattern.search(content):
        current_value = m.group(2)
        if current_value.lower() != "lowest":
            content = explicit_pattern.sub(r"\1lowest", content)
            changes.append(
                f"Changed PrivilegesRequired from '{current_value}' to 'lowest'"
            )
        else:
            changes.append("PrivilegesRequired=lowest was already set (no change needed)")
    else:
        content = re.sub(
            r"(\[Setup\]\s*\n)",
            r"\1PrivilegesRequired=lowest\n",
            content,
            count=1,
            flags=re.IGNORECASE,
        )
        changes.append("Inserted PrivilegesRequired=lowest after [Setup] header")

    # ------------------------------------------------------------------
    # 2. Remove PrivilegesRequiredOverridesAllowed
    #
    # This directive lets the user switch between per-user and machine-wide
    # install during setup.  Removing it locks the installer to current-user
    # mode, giving this build unambiguous no-UAC semantics.
    # ------------------------------------------------------------------
    overrides_pattern = re.compile(
        r"^PrivilegesRequiredOverridesAllowed\s*=.*\n?",
        re.MULTILINE | re.IGNORECASE,
    )
    if overrides_pattern.search(content):
        content = overrides_pattern.sub("", content)
        changes.append(
            "Removed PrivilegesRequiredOverridesAllowed "
            "(installer is now strictly current-user-only)"
        )

    # ------------------------------------------------------------------
    # 3. Append "-no-uac" to OutputBaseFilename (idempotent)
    #
    # Makes the resulting .exe filename clearly different from the official
    # darktable installer so users cannot confuse the two.
    # ------------------------------------------------------------------
    output_pattern = re.compile(
        r"^(OutputBaseFilename\s*=\s*.+?)(\s*)$",
        re.MULTILINE | re.IGNORECASE,
    )
    output_match = output_pattern.search(content)
    if output_match and not output_match.group(1).lower().endswith("-no-uac"):
        content = output_pattern.sub(r"\1-no-uac\2", content)
        changes.append("Appended '-no-uac' to OutputBaseFilename")

    # ------------------------------------------------------------------
    # Verification — abort if the critical change did not take effect
    # ------------------------------------------------------------------
    verified_lowest = re.search(
        r"^PrivilegesRequired\s*=\s*lowest\s*$",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if not verified_lowest:
        print(
            "ERROR: PrivilegesRequired=lowest was not set correctly.\n"
            "Aborting to prevent building a UAC-triggering installer.",
            file=sys.stderr,
        )
        sys.exit(1)

    overrides_still_present = re.search(
        r"^PrivilegesRequiredOverridesAllowed\s*=",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if overrides_still_present:
        print(
            "ERROR: PrivilegesRequiredOverridesAllowed is still present.\n"
            "The installer could allow the user to switch to admin mode.",
            file=sys.stderr,
        )
        sys.exit(1)

    if content == original:
        print(
            "WARNING: no changes were applied.  The template may already be "
            "in no-UAC mode, or the expected patterns were not found.",
            file=sys.stderr,
        )

    # ------------------------------------------------------------------
    # Write back the modified template
    # ------------------------------------------------------------------
    with open(iss_in_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"no-UAC patch applied successfully to: {iss_in_path}")
    for change in changes:
        print(f"  + {change}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/darktable.iss.in>", file=sys.stderr)
        sys.exit(1)

    apply_no_uac_patch(sys.argv[1])

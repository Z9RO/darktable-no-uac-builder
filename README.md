# darktable Windows no-UAC Installer Builder

This repository contains **unofficial CI build scripts** that produce a
darktable Windows installer configured for **current-user (per-user)
installation** — no UAC elevation prompt, no write access to system
directories or `HKLM`.

---

## What this is (and is not)

| This is | This is NOT |
|---------|-------------|
| A lightweight CI overlay that downloads darktable source and applies a minimal installer patch | A darktable fork |
| A builder that produces a per-user install package | A portable / standalone edition of darktable |
| A UAC-free installer build | A UAC bypass tool |
| An unofficial build script | An official darktable release channel |

This project does **not** modify any darktable functional code.  The only
change applied to the upstream source is to the Windows Inno Setup installer
script (`packaging/windows/darktable.iss.in`), which is patched to:

1. Set `PrivilegesRequired=lowest` — the installer runs without admin rights.
2. Remove `PrivilegesRequiredOverridesAllowed` — the user cannot switch to a
   machine-wide install during setup, keeping the build unambiguously
   current-user-only.
3. Append `-no-uac` to the output filename so the artifact is clearly
   distinguishable from the official installer.

All registry entries in darktable's installer already use `HKA` (HKEY_AUTO),
which maps automatically to `HKCU` when running without admin rights.  The
install directory uses `{autopf}`, which resolves to
`%LOCALAPPDATA%\Programs` in non-admin mode.  No additional code changes are
required.

---

## How to trigger a build

1. Open the **Actions** tab in this repository.
2. Select the **"Build darktable no-UAC Windows Installer"** workflow.
3. Click **"Run workflow"**.
4. Enter the darktable upstream ref you want to build:
   - A release tag: `release-4.8.0`
   - A full commit SHA: `abc1234...`
5. Click **"Run workflow"** to start the job.

The job runs on a `windows-latest` GitHub-hosted runner and takes
approximately 90–180 minutes to complete (darktable is a large C/C++ project
with many dependencies).

---

## How to download the artifact

1. Open the completed workflow run in the **Actions** tab.
2. Scroll to the **Artifacts** section at the bottom of the run summary page.
3. Download **`darktable-windows-no-uac-<short-sha>`**.

The ZIP archive contains a single `.exe` installer with a name like:

```
darktable-4.8.0-win64-no-uac.exe
```

---

## How to confirm the actual commit that was built

Each workflow run records the exact upstream commit in two places:

1. **Step log** — the "Record upstream commit" step prints both the input ref
   and the resolved commit SHA.
2. **Job summary** — the summary table at the bottom of the run page includes
   `Actual upstream commit`.

This ensures that what you requested and what was actually compiled are always
traceable.

---

## How to verify the installer does not trigger UAC

After installing, you can confirm the package used per-user mode:

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\
```

Should contain a darktable entry (not under `HKLM`).

The installer itself should not have shown a UAC prompt.  If it did, something
went wrong with the patch — please open an issue.

You can also inspect the `.exe` with [Inno Setup Unpacker](https://github.com/cracker0dks/InnoSetupUnpacker)
or [innounp](http://innounp.sourceforge.net/) and confirm
`PrivilegesRequired=lowest` in the embedded setup script.

---

## Specifying a darktable release tag

darktable tags its releases as `release-X.Y.Z`, for example:

| Version | Tag |
|---------|-----|
| 4.8.0 | `release-4.8.0` |
| 4.6.1 | `release-4.6.1` |
| 4.4.2 | `release-4.4.2` |

You can find all tags at:
<https://github.com/darktable-org/darktable/tags>

Alternatively, you can pass any full commit SHA to build from an arbitrary
point in the darktable history.

---

## Known limitations

This project only changes whether the **main program installer** requires
administrator rights.  It cannot address:

- Camera driver installation (gphoto2 / libusb / Zadig / WinUSB).  Tethering
  (connected shooting) may still require admin rights to install USB drivers.
- System-wide file associations (require `HKLM`).
- Shared / machine-wide installation for multiple users.
- Enterprise Group Policy restrictions.
- Antivirus / Windows SmartScreen warnings on unsigned installers.

The installer built here is **unsigned**.  Windows SmartScreen may display a
"Windows protected your PC" dialog the first time it is run.  Click
**"More info → Run anyway"** to proceed.

---

## Risk: upstream installer template changes

If the darktable project changes `packaging/windows/darktable.iss.in` in a
way that the patch script (`patches/apply_no_uac.py`) no longer recognises,
the workflow will **fail loudly** rather than produce a silently-broken
installer.  The patch script verifies that:

- `PrivilegesRequired=lowest` is present after patching.
- `PrivilegesRequiredOverridesAllowed` is absent after patching.

If either check fails the job exits immediately with a non-zero status.

When this happens, update `patches/apply_no_uac.py` to match the new
template structure and re-run the workflow.

---

## GPL obligations

darktable is licensed under the GNU General Public License v3 (GPL-3.0).
By downloading and distributing the installer produced by this workflow you
accept the obligations of the GPL:

- You must provide (or offer to provide) the corresponding source code.
- The source code for the exact commit built is always available from the
  upstream darktable repository at
  <https://github.com/darktable-org/darktable>.
- The build scripts in this repository are also released under GPL-3.0
  (see [LICENSE](LICENSE)).

This project does **not** add any additional restrictions beyond those already
imposed by the GPL.

---

## Disclaimer

This is an **unofficial**, **unsupported** build.  It is not endorsed by or
affiliated with the darktable project or its developers.  Use at your own risk.

For official darktable releases visit <https://darktable.org/>.
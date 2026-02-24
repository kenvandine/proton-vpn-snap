#!/usr/bin/env python3
"""
Patch session_monitor.py for strict snap confinement.

In a strictly confined snap, AppArmor blocks D-Bus access to
org.freedesktop.login1 (systemd-logind), causing _setup() to raise
dbus.exceptions.DBusException.

This patch makes SessionMonitor.enable() and is_session_unlocked degrade
gracefully when logind is inaccessible, so the app doesn't crash. Session-unlock
VPN reconnection won't work (the login-session-observe plug can restore it),
but all other functionality is unaffected.
"""
import sys

PATH = "usr/lib/python3/dist-packages/proton/vpn/app/gtk/services/reconnector/session_monitor.py"

# --- Patch enable(): swallow logind access errors ---

OLD_ENABLE = """\
        if not self._session_object_path:
            self._setup()

        self._signal_receiver = self._bus.add_signal_receiver(\
"""

NEW_ENABLE = """\
        if not self._session_object_path:
            try:
                self._setup()
            except Exception:
                # Logind is inaccessible (AppArmor in strict snap confinement).
                # Session-unlock reconnection won't work; everything else is fine.
                return

        self._signal_receiver = self._bus.add_signal_receiver(\
"""

# --- Patch is_session_unlocked: assume unlocked when logind is inaccessible ---

OLD_UNLOCKED = """\
        if not self._session_object_path:
            self._setup()

        active_session = self._bus.get_object(BUS_NAME, self._session_object_path)\
"""

NEW_UNLOCKED = """\
        if not self._session_object_path:
            try:
                self._setup()
            except Exception:
                # Logind is inaccessible; assume session is unlocked so reconnection
                # can proceed when network comes up.
                return True

        active_session = self._bus.get_object(BUS_NAME, self._session_object_path)\
"""

with open(PATH) as f:
    content = f.read()

failed = False

if OLD_ENABLE not in content:
    print(f"ERROR: enable() pattern not found in {PATH}", file=sys.stderr)
    failed = True

if OLD_UNLOCKED not in content:
    print(f"ERROR: is_session_unlocked pattern not found in {PATH}", file=sys.stderr)
    failed = True

if failed:
    print("The upstream source may have changed — review the patch.", file=sys.stderr)
    sys.exit(1)

content = content.replace(OLD_ENABLE, NEW_ENABLE, 1)
content = content.replace(OLD_UNLOCKED, NEW_UNLOCKED, 1)

with open(PATH, "w") as f:
    f.write(content)

print(f"Patched {PATH}")

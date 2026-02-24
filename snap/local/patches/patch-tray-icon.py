#!/usr/bin/env python3
"""
Patch tray_icon.py for strict snap confinement.

The StatusNotifierItem bus name is generated as:
    org.kde.StatusNotifierItem-{app_id}-{id(self)}

id(self) is a Python object address — a large integer (up to 15+ digits) that
exceeds the pattern snapd generates in AppArmor for dbus slot name suffixes
(which covers up to 10 consecutive digits).

Replace id(self) with os.getpid() so the bus name suffix is the process PID,
which is always ≤7 digits on Linux and is matched correctly by the snapd-
generated AppArmor rule:
    name=org.kde.StatusNotifierItem-proton.vpn.app.gtk{_,-}[1-9][0-9...]*
"""
import sys

PATH = "usr/lib/python3/dist-packages/proton/vpn/app/gtk/widgets/main/tray_icon.py"

OLD_IMPORT = """\
import dbus
import dbus.service
import dbus.mainloop.glib\
"""

NEW_IMPORT = """\
import os
import dbus
import dbus.service
import dbus.mainloop.glib\
"""

OLD_BUS_NAME = \
    '        self.bus_name_str = f"org.kde.StatusNotifierItem-{tray_icon.app_id}-{id(self)}"'

NEW_BUS_NAME = \
    '        self.bus_name_str = f"org.kde.StatusNotifierItem-{tray_icon.app_id}-{os.getpid()}"'

with open(PATH) as f:
    content = f.read()

failed = False

if OLD_IMPORT not in content:
    print(f"ERROR: import block pattern not found in {PATH}", file=sys.stderr)
    failed = True

if OLD_BUS_NAME not in content:
    print(f"ERROR: bus_name_str pattern not found in {PATH}", file=sys.stderr)
    failed = True

if failed:
    print("The upstream source may have changed — review the patch.", file=sys.stderr)
    sys.exit(1)

content = content.replace(OLD_IMPORT, NEW_IMPORT, 1)
content = content.replace(OLD_BUS_NAME, NEW_BUS_NAME, 1)

with open(PATH, "w") as f:
    f.write(content)

print(f"Patched {PATH}")

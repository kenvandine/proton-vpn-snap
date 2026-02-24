#!/usr/bin/env python3
"""
Two patches for tray_indicator.py in a strictly confined snap:

1. _can_tray_be_used(): when _gnome_shell_list_extensions() returns None (AppArmor
   blocks the D-Bus call to org.gnome.Shell.Extensions), assume appindicator is
   available rather than crashing with AttributeError.

2. setup(): wrap TrayIcon.setup() so that D-Bus failures (e.g. AppArmor blocking
   ownership of org.kde.StatusNotifierItem-*) raise TrayIndicatorNotSupported,
   which app.py already catches and handles by disabling the tray gracefully.
"""
import sys

PATH = "usr/lib/python3/dist-packages/proton/vpn/app/gtk/widgets/main/tray_indicator.py"

# --- Patch 1: wrap TrayIcon.setup() so D-Bus failures raise TrayIndicatorNotSupported ---

OLD_SETUP = """\
        if self._tray is None:
            self._tray = TrayIcon()
            self._tray.setup()\
"""

NEW_SETUP = """\
        if self._tray is None:
            self._tray = TrayIcon()
            try:
                self._tray.setup()
            except Exception as e:
                raise TrayIndicatorNotSupported(
                    f"Failed to set up system tray: {e}"
                ) from e\
"""

OLD = """\
            gnome_extensions = self._gnome_shell_list_extensions()
            ubuntu_extension = gnome_extensions.get(UBUNTU_INDICATOR_EXTENSION)
            default_extension = gnome_extensions.get(DEFAULT_INDICATOR_EXTENSION)

            # Since the extension is part of the system we don't care about the
            # user_extension_disabled value.
            enable_for_ubuntu = ubuntu_extension \\
                and ubuntu_extension.get("state") == ACTIVE_STATE

            # For the rest we take user_extension_disabled into consideration
            # since it's not installed by default on the system and is dependent
            # on user intention.
            enable_for_default = default_extension \\
                and not self._disabled_user_extension() \\
                and default_extension.get("state") == ACTIVE_STATE

            if enable_for_ubuntu or enable_for_default:
                self._app_indicator_available = True\
"""

NEW = """\
            gnome_extensions = self._gnome_shell_list_extensions()
            if gnome_extensions is None:
                # Cannot query extensions (AppArmor blocks D-Bus in strict snap).
                # Assume appindicator is available.
                self._app_indicator_available = True
            else:
                ubuntu_extension = gnome_extensions.get(UBUNTU_INDICATOR_EXTENSION)
                default_extension = gnome_extensions.get(DEFAULT_INDICATOR_EXTENSION)

                # Since the extension is part of the system we don't care about the
                # user_extension_disabled value.
                enable_for_ubuntu = ubuntu_extension \\
                    and ubuntu_extension.get("state") == ACTIVE_STATE

                # For the rest we take user_extension_disabled into consideration
                # since it's not installed by default on the system and is dependent
                # on user intention.
                enable_for_default = default_extension \\
                    and not self._disabled_user_extension() \\
                    and default_extension.get("state") == ACTIVE_STATE

                if enable_for_ubuntu or enable_for_default:
                    self._app_indicator_available = True\
"""

with open(PATH) as f:
    content = f.read()

failed = False

if OLD_SETUP not in content:
    print(f"ERROR: setup() pattern not found in {PATH}", file=sys.stderr)
    failed = True

if OLD not in content:
    print(f"ERROR: _can_tray_be_used() pattern not found in {PATH}", file=sys.stderr)
    failed = True

if failed:
    print("The upstream source may have changed — review the patch.", file=sys.stderr)
    sys.exit(1)

content = content.replace(OLD_SETUP, NEW_SETUP, 1)
content = content.replace(OLD, NEW, 1)

with open(PATH, "w") as f:
    f.write(content)

print(f"Patched {PATH}")

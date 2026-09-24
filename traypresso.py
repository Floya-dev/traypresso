import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3

from duration import PRESET_DURATIONS, PRESET_MINUTES, parse_duration
from inhibitor import Inhibitor
import settings as settings_mod

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
ICON_NAME = "traypresso_v2"
REPO_URL = "https://github.com/Floya-dev/traypresso"


class TraypressoApp:
    def __init__(self):
        self.settings = settings_mod.load_settings()
        self.inhibitor = Inhibitor()
        self._build_window()
        self._build_indicator()
        self._apply_settings_to_widgets()

    def _build_window(self):
        self.window = Gtk.Window(title="traypresso")
        self.window.set_border_width(12)
        self.window.set_resizable(False)
        self.window.connect("delete-event", self.on_window_delete)
        self.window.connect("key-press-event", self.on_key_press)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window.add(box)

        box.pack_start(Gtk.Label(label="Duration", xalign=0), False, False, 0)

        self.duration_combo = Gtk.ComboBoxText()
        for _, label in PRESET_DURATIONS:
            self.duration_combo.append_text(label)
        box.pack_start(self.duration_combo, False, False, 0)

        self.duration_entry = Gtk.Entry()
        self.duration_entry.set_placeholder_text("e.g. 12m or 2.5h")
        box.pack_start(self.duration_entry, False, False, 0)

        lid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lid_label = Gtk.Label(label="_Ignore lid", use_underline=True)
        self.lid_toggle = Gtk.Switch()
        lid_label.set_mnemonic_widget(self.lid_toggle)
        lid_box.pack_start(lid_label, False, False, 0)
        lid_box.pack_start(self.lid_toggle, False, False, 0)
        box.pack_start(lid_box, False, False, 0)

        self.start_button = Gtk.Button(label="Start")
        self.start_button.connect("clicked", self.on_start_stop_clicked)
        self.start_button.set_can_default(True)
        box.pack_start(self.start_button, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        settings_button = Gtk.Button(label="Settings")
        settings_button.connect("clicked", self.on_settings_clicked)
        quit_button = Gtk.Button(label="Quit")
        quit_button.connect("clicked", self.on_quit)
        button_box.pack_start(settings_button, True, True, 0)
        button_box.pack_start(quit_button, True, True, 0)
        box.pack_start(button_box, False, False, 0)

        self.window.set_default(self.start_button)

    def _build_indicator(self):
        self.indicator = AppIndicator3.Indicator.new(
            "traypresso", ICON_NAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_icon_theme_path(ICON_DIR)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()
        open_item = Gtk.MenuItem(label="Open traypresso")
        open_item.connect("activate", self.on_indicator_open)
        menu.append(open_item)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit)
        menu.append(quit_item)
        menu.show_all()
        self.indicator.set_menu(menu)

    def _apply_settings_to_widgets(self):
        last = self.settings["last_duration_minutes"]
        self.duration_combo.set_active(
            PRESET_MINUTES.index(last) if last in PRESET_MINUTES else 0
        )
        self.duration_entry.set_text(
            "Indefinite" if last is None else _format_minutes(last)
        )
        self.lid_toggle.set_active(self.settings["ignore_lid"])
        self._apply_duration_mode()

    def _apply_duration_mode(self):
        custom = self.settings["custom_duration_mode"]
        self.duration_combo.set_visible(not custom)
        self.duration_entry.set_visible(custom)

    def _get_selected_duration_minutes(self):
        if self.settings["custom_duration_mode"]:
            return parse_duration(self.duration_entry.get_text())
        return PRESET_MINUTES[self.duration_combo.get_active()]

    def on_start_stop_clicked(self, _button):
        if self.inhibitor.is_running():
            self.inhibitor.stop()
            self._set_running_ui(False)
            return
        try:
            minutes = self._get_selected_duration_minutes()
        except ValueError as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Invalid duration: {e}",
            )
            dialog.format_secondary_text("Try formats like 12m, 2.5h, 90, or Indefinite.")
            dialog.run()
            dialog.destroy()
            return
        ignore_lid = self.lid_toggle.get_active()
        try:
            self.inhibitor.start(ignore_lid, minutes, on_expire=self._on_expire)
        except OSError as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Couldn't start systemd-inhibit: {e}",
            )
            dialog.run()
            dialog.destroy()
            return
        self.settings["last_duration_minutes"] = minutes
        self.settings["ignore_lid"] = ignore_lid
        self._set_running_ui(True)

    def _on_expire(self):
        self._set_running_ui(False)

    def _set_running_ui(self, running: bool):
        self.start_button.set_label("Stop" if running else "Start")
        self.duration_combo.set_sensitive(not running)
        self.duration_entry.set_sensitive(not running)
        self.lid_toggle.set_sensitive(not running)

    def on_settings_clicked(self, _button):
        dialog = Gtk.Dialog(title="Settings", transient_for=self.window, modal=True)
        dialog.set_resizable(False)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        content = dialog.get_content_area()
        content.set_border_width(12)
        content.set_spacing(8)

        content.add(Gtk.Label(label="traypresso — keeps your laptop awake"))
        content.add(Gtk.LinkButton.new_with_label(REPO_URL, "traypresso on GitHub"))

        custom_check = Gtk.CheckButton(label="Use custom duration input")
        custom_check.set_active(self.settings["custom_duration_mode"])
        custom_check.connect("toggled", self.on_custom_mode_toggled)
        content.add(custom_check)

        content.show_all()
        dialog.run()
        dialog.destroy()

    def on_custom_mode_toggled(self, check_button):
        self.settings["custom_duration_mode"] = check_button.get_active()
        self._apply_duration_mode()

    def on_window_delete(self, _window, _event):
        self.window.hide()
        return True  # keep running in tray, don't destroy

    def on_key_press(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.window.hide()
            return True
        return False

    def on_indicator_open(self, _item):
        self.window.show_all()
        self._apply_duration_mode()
        self.window.present()

    def on_quit(self, *_args):
        self.inhibitor.stop()
        settings_mod.save_settings(self.settings)
        Gtk.main_quit()

    def run(self):
        Gtk.main()


def _format_minutes(minutes: float) -> str:
    return str(int(minutes)) if minutes == int(minutes) else str(minutes)


if __name__ == "__main__":
    TraypressoApp().run()

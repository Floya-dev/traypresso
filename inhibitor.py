import subprocess

from gi.repository import GLib


class Inhibitor:
    def __init__(self):
        self._proc = None
        self._timer_id = None

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, ignore_lid: bool, duration_minutes, on_expire=None):
        self.stop()
        what = "handle-lid-switch:sleep:idle" if ignore_lid else "sleep:idle"
        cmd = [
            "systemd-inhibit",
            f"--what={what}",
            "--who=traypresso",
            "--why=keep running",
            "sleep",
            "infinity",
        ]
        self._proc = subprocess.Popen(cmd)
        if duration_minutes is not None:
            self._timer_id = GLib.timeout_add(
                int(duration_minutes * 60_000), self._on_timeout, on_expire
            )

    def _on_timeout(self, on_expire):
        self._timer_id = None
        self.stop()
        if on_expire:
            on_expire()
        return False  # one-shot GLib source

    def stop(self):
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                # ponytail: synchronous wait blocks UI briefly; switch to GLib.child_watch_add if this is ever noticed
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

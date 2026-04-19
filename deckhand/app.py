from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import rumps

from deckhand import config, logger, sync


def _asset(name: str) -> str:
    """Return absolute path to a bundled asset, works both frozen and in dev."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts --add-data files relative to sys._MEIPASS
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return str(base / "assets" / name)


_ICON = _asset("icon.png")


class DeckhAndApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("", icon=_ICON, template=True, quit_button="Quit")
        self._updater_controller = None
        self._last_synced = rumps.MenuItem("Never synced")
        self._last_synced.set_callback(None)
        self.menu = [
            rumps.MenuItem("Sync Now", callback=self.on_sync_now),
            None,
            rumps.MenuItem("Check for Updates\u2026", callback=self.on_check_updates),
            rumps.MenuItem("View Log", callback=self.on_view_log),
            rumps.MenuItem("Change Sync Folder\u2026", callback=self.on_change_folder),
            None,
            self._last_synced,
        ]
        self._init_sparkle()

    def _init_sparkle(self) -> None:
        """Load Sparkle.framework from the app bundle and start the auto-updater."""
        try:
            from Foundation import NSBundle
            import objc

            frameworks_path = NSBundle.mainBundle().privateFrameworksPath()
            sparkle_path = os.path.join(frameworks_path, "Sparkle.framework")
            sparkle_bundle = NSBundle.bundleWithPath_(sparkle_path)

            if sparkle_bundle and sparkle_bundle.load():
                SPUStandardUpdaterController = objc.lookUpClass("SPUStandardUpdaterController")
                # Keep a strong reference — GC will kill it otherwise
                self._updater_controller = (
                    SPUStandardUpdaterController
                    .alloc()
                    .initWithUpdaterDelegate_userDriverDelegate_(None, None)
                )
        except Exception:
            pass  # Running outside bundle (dev mode) — gracefully skip

    def on_check_updates(self, _: rumps.MenuItem) -> None:
        if self._updater_controller:
            self._updater_controller.checkForUpdates_(None)

    def on_sync_now(self, _: rumps.MenuItem) -> None:
        try:
            result = sync.run(on_need_folder=self._pick_folder)
            n_in = len(result["imported"])
            n_out = len(result["exported"])
            n_rm = len(result.get("removed", []))
            parts = [f"{n_in} imported", f"{n_out} exported"]
            if n_rm:
                parts.append(f"{n_rm} stale removed")
            rumps.notification(
                title="Deckhand",
                subtitle="Sync complete",
                message=", ".join(parts),
            )
            self._last_synced.title = "Last synced: just now"
        except RuntimeError as exc:
            logger.error(traceback.format_exc())
            rumps.notification(
                title="Deckhand",
                subtitle="Sync failed",
                message=str(exc),
            )
            self._open_log_window()
        except Exception:
            logger.error(traceback.format_exc())
            rumps.notification(
                title="Deckhand",
                subtitle="Sync failed",
                message="An unexpected error occurred. Check the log for details.",
            )
            self._open_log_window()

    def on_view_log(self, _: rumps.MenuItem) -> None:
        self._open_log_window()

    def on_change_folder(self, _: rumps.MenuItem) -> None:
        path = self._pick_folder()
        if path:
            config.set_drive_folder(path)
            rumps.notification(
                title="Deckhand",
                subtitle="Sync folder updated",
                message=path,
            )

    def _open_log_window(self) -> None:
        content = logger.tail(100) or "No log entries yet."
        rumps.alert(title="Deckhand Log", message=content)

    def _pick_folder(self) -> str | None:
        from AppKit import NSOpenPanel  # available via PyObjC bundled with macOS Python

        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(True)
        panel.setCanChooseFiles_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setMessage_("Choose your AnkiSync folder inside Google Drive")
        if panel.runModal():
            return panel.URLs()[0].path()
        return None

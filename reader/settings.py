"""
COMIO — User Settings & Preferences
Uses QSettings for persistent cross-session configuration.
"""

import os
from pathlib import Path
from PyQt6.QtCore import QSettings


# Default paths
DEFAULT_LIBRARY_PATH = str(Path.home() / "COMIO Library")
DEFAULT_DOWNLOAD_PATH = str(Path.home() / "COMIO Library" / "Downloads")


class Settings:
    """Manages user preferences with QSettings backend."""

    def __init__(self):
        self._settings = QSettings("COMIO", "ComicReader")

    # ── Theme ──────────────────────────────────────────────────────────

    @property
    def theme(self) -> str:
        return self._settings.value("appearance/theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self._settings.setValue("appearance/theme", value)

    # ── Reading ────────────────────────────────────────────────────────

    @property
    def reading_direction(self) -> str:
        """'ltr' for western, 'rtl' for manga."""
        return self._settings.value("reading/direction", "ltr")

    @reading_direction.setter
    def reading_direction(self, value: str):
        self._settings.setValue("reading/direction", value)

    @property
    def view_mode(self) -> str:
        """'single', 'double', or 'vertical'."""
        return self._settings.value("reading/view_mode", "single")

    @view_mode.setter
    def view_mode(self, value: str):
        self._settings.setValue("reading/view_mode", value)

    @property
    def fit_mode(self) -> str:
        """'width', 'height', 'page', or 'original'."""
        return self._settings.value("reading/fit_mode", "width")

    @fit_mode.setter
    def fit_mode(self, value: str):
        self._settings.setValue("reading/fit_mode", value)

    @property
    def zoom_level(self) -> float:
        return float(self._settings.value("reading/zoom_level", 1.0))

    @zoom_level.setter
    def zoom_level(self, value: float):
        self._settings.setValue("reading/zoom_level", value)

    @property
    def scroll_speed(self) -> int:
        return int(self._settings.value("reading/scroll_speed", 3))

    @scroll_speed.setter
    def scroll_speed(self, value: int):
        self._settings.setValue("reading/scroll_speed", value)

    # ── Library ────────────────────────────────────────────────────────

    @property
    def library_path(self) -> str:
        return self._settings.value("library/path", DEFAULT_LIBRARY_PATH)

    @library_path.setter
    def library_path(self, value: str):
        self._settings.setValue("library/path", value)

    @property
    def download_path(self) -> str:
        return self._settings.value("library/download_path", DEFAULT_DOWNLOAD_PATH)

    @download_path.setter
    def download_path(self, value: str):
        self._settings.setValue("library/download_path", value)

    @property
    def auto_scan(self) -> bool:
        return self._settings.value("library/auto_scan", True, type=bool)

    @auto_scan.setter
    def auto_scan(self, value: bool):
        self._settings.setValue("library/auto_scan", value)

    # ── Window State ───────────────────────────────────────────────────

    @property
    def window_geometry(self) -> bytes:
        return self._settings.value("window/geometry", b"")

    @window_geometry.setter
    def window_geometry(self, value: bytes):
        self._settings.setValue("window/geometry", value)

    @property
    def window_state(self) -> bytes:
        return self._settings.value("window/state", b"")

    @window_state.setter
    def window_state(self, value: bytes):
        self._settings.setValue("window/state", value)

    @property
    def sidebar_visible(self) -> bool:
        return self._settings.value("window/sidebar_visible", True, type=bool)

    @sidebar_visible.setter
    def sidebar_visible(self, value: bool):
        self._settings.setValue("window/sidebar_visible", value)

    @property
    def last_opened_file(self) -> str:
        return self._settings.value("history/last_opened", "")

    @last_opened_file.setter
    def last_opened_file(self, value: str):
        self._settings.setValue("history/last_opened", value)

    # ── Recent Files ───────────────────────────────────────────────────

    @property
    def recent_files(self) -> list:
        return self._settings.value("history/recent_files", []) or []

    def add_recent_file(self, file_path: str, max_items: int = 10):
        """Add a file to the recent files list."""
        recent = self.recent_files
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self._settings.setValue("history/recent_files", recent[:max_items])

    # ── Bookmarks ──────────────────────────────────────────────────────

    def get_bookmark(self, file_path: str) -> int:
        """Get the bookmarked page for a file."""
        bookmarks = self._settings.value("bookmarks/pages", {}) or {}
        return int(bookmarks.get(file_path, 0))

    def set_bookmark(self, file_path: str, page: int):
        """Set a bookmark for a file."""
        bookmarks = self._settings.value("bookmarks/pages", {}) or {}
        bookmarks[file_path] = page
        self._settings.setValue("bookmarks/pages", bookmarks)

    # ── Internet Archive ───────────────────────────────────────────────

    @property
    def ia_results_per_page(self) -> int:
        return int(self._settings.value("ia/results_per_page", 20))

    @ia_results_per_page.setter
    def ia_results_per_page(self, value: int):
        self._settings.setValue("ia/results_per_page", value)

    # ── Utility ────────────────────────────────────────────────────────

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.library_path, exist_ok=True)
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(os.path.join(self.library_path, ".thumbnails"), exist_ok=True)

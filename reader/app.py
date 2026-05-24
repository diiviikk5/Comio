"""
COMIO — Main Application Window
Orchestrates library, viewer, IA browser, and download manager.
"""

import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QToolBar, QStatusBar, QLabel,
    QPushButton, QLineEdit, QFrame, QSplitter,
    QMessageBox, QFileDialog, QDockWidget, QListWidget,
    QListWidgetItem, QProgressBar, QSizePolicy, QMenu,
    QToolButton, QApplication
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QPixmap, QIcon, QShortcut, QFont
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal

from settings import Settings
from themes import get_theme
from comic_loader import ComicBook
from viewer import ComicViewer, PageNavigationBar
from library import LibraryView
from ia_client import IASearchThread, IAItemDetailsThread, IAComic, COLLECTIONS
from downloader import DownloadManager


class IABrowserPanel(QWidget):
    """Internet Archive comic browser panel."""
    download_requested = pyqtSignal(object)  # IAComic

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._search_thread = IASearchThread(self)
        self._search_thread.results_ready.connect(self._on_results)
        self._search_thread.error_occurred.connect(self._on_error)
        self._search_thread.search_started.connect(self._on_search_start)

        self._details_thread = IAItemDetailsThread(self)
        self._details_thread.details_ready.connect(self._on_details)

        self._comics: list[IAComic] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet("background-color: #111111; border-bottom: 1px solid #1a1a1a;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("🌐 Internet Archive")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #3B82F6; background: transparent;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        # Collection dropdown
        self._collection_btn = QToolButton()
        self._collection_btn.setText("📂 Collections")
        self._collection_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._collection_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QToolButton:hover { border-color: #3B82F6; }
        """)
        coll_menu = QMenu(self)
        for name in COLLECTIONS:
            action = coll_menu.addAction(name)
            action.triggered.connect(lambda checked, n=name: self._search_collection(n))
        self._collection_btn.setMenu(coll_menu)
        h_layout.addWidget(self._collection_btn)

        layout.addWidget(header)

        # Search bar
        search_bar = QWidget()
        search_bar.setFixedHeight(50)
        search_bar.setStyleSheet("background-color: #0d0d0d;")
        s_layout = QHBoxLayout(search_bar)
        s_layout.setContentsMargins(16, 8, 16, 8)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search comics on Internet Archive...")
        self._search_input.returnPressed.connect(self._do_search)
        s_layout.addWidget(self._search_input)

        search_btn = QPushButton("Search")
        search_btn.setFixedSize(80, 34)
        search_btn.clicked.connect(self._do_search)
        s_layout.addWidget(search_btn)

        layout.addWidget(search_bar)

        # Status
        self._status_label = QLabel("Search for comics or browse a collection")
        self._status_label.setStyleSheet("color: #666; padding: 8px 16px; font-size: 12px; background: transparent;")
        layout.addWidget(self._status_label)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setStyleSheet("""
            QListWidget {
                background-color: #0d0d0d;
                border: none;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #1a1a1a;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #1a1a1a;
                border-left: 3px solid #3B82F6;
            }
            QListWidget::item:hover {
                background-color: #151515;
            }
        """)
        self._results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._results_list)

    def _do_search(self):
        query = self._search_input.text().strip()
        if query:
            self._search_thread.search(
                query,
                max_results=self._settings.ia_results_per_page
            )

    def _search_collection(self, collection_name: str):
        self._status_label.setText(f"Searching {collection_name}...")
        self._search_input.clear()
        self._search_thread.search(
            "",  # Empty query, collection filter applied internally
            max_results=self._settings.ia_results_per_page,
            sort="downloads desc"
        )

    def _on_search_start(self):
        self._status_label.setText("🔍 Searching Internet Archive...")
        self._results_list.clear()
        self._comics.clear()

    def _on_results(self, results: list):
        self._comics = results
        self._results_list.clear()

        if not results:
            self._status_label.setText("No results found. Try a different search.")
            return

        self._status_label.setText(f"Found {len(results)} comics")

        for comic in results:
            item = QListWidgetItem()
            text = f"📚 {comic.title}"
            if comic.creator:
                text += f"\n   👤 {comic.creator}"
            if comic.date:
                text += f"  |  📅 {comic.date[:10]}"
            if comic.downloads:
                text += f"  |  ⬇️ {comic.downloads:,} downloads"
            item.setText(text)
            item.setData(Qt.ItemDataRole.UserRole, comic)
            self._results_list.addItem(item)

    def _on_error(self, error: str):
        self._status_label.setText(f"❌ Error: {error}")

    def _on_item_double_clicked(self, item: QListWidgetItem):
        comic = item.data(Qt.ItemDataRole.UserRole)
        if comic:
            self._status_label.setText(f"Fetching file list for {comic.title}...")
            self._details_thread.fetch(comic.identifier)
            # Store reference to find comic later
            self._pending_comic = comic

    def _on_details(self, identifier: str, files: list):
        if hasattr(self, '_pending_comic') and self._pending_comic.identifier == identifier:
            self._pending_comic.files = files
            best = self._pending_comic.get_best_download()
            if best:
                reply = QMessageBox.question(
                    self,
                    "Download Comic",
                    f"Download '{self._pending_comic.title}'?\n"
                    f"File: {best['name']}\n"
                    f"Size: {best.get('size', 0) / (1024*1024):.1f} MB",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.download_requested.emit(self._pending_comic)
                    self._status_label.setText(f"⬇️ Downloading {self._pending_comic.title}...")
            else:
                self._status_label.setText("No downloadable comic files found for this item.")


class DownloadPanel(QWidget):
    """Panel showing download progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("⬇️ Downloads")
        header.setFixedHeight(40)
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #FB923C; padding: 8px 16px; background: #111;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget { background: #0d0d0d; border: none; }
            QListWidget::item { padding: 8px 16px; border-bottom: 1px solid #1a1a1a; color: #ccc; }
        """)
        layout.addWidget(self._list)

    def add_download(self, title: str, url: str):
        item = QListWidgetItem(f"⬇️ {title}")
        item.setData(Qt.ItemDataRole.UserRole, url)
        self._list.addItem(item)

    def update_download(self, url: str, progress: float, speed_str: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == url:
                title = item.text().split(" — ")[0]
                item.setText(f"{title} — {progress:.0f}% ({speed_str})")
                break

    def complete_download(self, url: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == url:
                title = item.text().split(" — ")[0].replace("⬇️", "✅")
                item.setText(f"✅{title} — Complete")
                break


class ComioMainWindow(QMainWindow):
    """Main application window for COMIO Comic Reader."""

    def __init__(self):
        super().__init__()

        # Initialize core components
        self._settings = Settings()
        self._settings.ensure_directories()
        self._current_comic: Optional[ComicBook] = None
        self._download_manager = DownloadManager()
        self._download_manager.progress_updated.connect(self._on_download_progress)
        self._download_manager.download_completed.connect(self._on_download_completed)
        self._download_manager.download_failed.connect(self._on_download_failed)

        # Setup
        self.setWindowTitle("COMIO — Comic Reader")
        self.setMinimumSize(1000, 700)
        self.resize(1280, 800)

        # Apply theme
        self.setStyleSheet(get_theme(self._settings.theme))

        # Build UI
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central()
        self._setup_statusbar()
        self._setup_shortcuts()

        # Restore window state
        if self._settings.window_geometry:
            try:
                self.restoreGeometry(self._settings.window_geometry)
            except Exception:
                pass

        # Scan library on startup
        QTimer.singleShot(500, self._library_view.scan_library)

    def _setup_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = file_menu.addAction("Open Comic...")
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_file)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu("&View")

        self._fullscreen_action = view_menu.addAction("Fullscreen")
        self._fullscreen_action.setShortcut(QKeySequence("F11"))
        self._fullscreen_action.setCheckable(True)
        self._fullscreen_action.triggered.connect(self._toggle_fullscreen)

        view_menu.addSeparator()

        fit_width = view_menu.addAction("Fit Width")
        fit_width.setShortcut(QKeySequence("W"))
        fit_width.triggered.connect(lambda: self._set_fit_mode("width"))

        fit_height = view_menu.addAction("Fit Height")
        fit_height.setShortcut(QKeySequence("H"))
        fit_height.triggered.connect(lambda: self._set_fit_mode("height"))

        fit_page = view_menu.addAction("Fit Page")
        fit_page.setShortcut(QKeySequence("F"))
        fit_page.triggered.connect(lambda: self._set_fit_mode("page"))

        view_menu.addSeparator()

        single_page = view_menu.addAction("Single Page")
        single_page.setShortcut(QKeySequence("1"))
        single_page.triggered.connect(lambda: self._set_view_mode("single"))

        double_page = view_menu.addAction("Double Page")
        double_page.setShortcut(QKeySequence("2"))
        double_page.triggered.connect(lambda: self._set_view_mode("double"))

        view_menu.addSeparator()

        theme_menu = view_menu.addMenu("Theme")
        dark_action = theme_menu.addAction("Dark")
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        light_action = theme_menu.addAction("Light")
        light_action.triggered.connect(lambda: self._set_theme("light"))

        # Navigate menu
        nav_menu = menubar.addMenu("&Navigate")

        next_action = nav_menu.addAction("Next Page")
        next_action.setShortcut(QKeySequence("Right"))
        next_action.triggered.connect(self._next_page)

        prev_action = nav_menu.addAction("Previous Page")
        prev_action.setShortcut(QKeySequence("Left"))
        prev_action.triggered.connect(self._prev_page)

        nav_menu.addSeparator()

        first_action = nav_menu.addAction("First Page")
        first_action.setShortcut(QKeySequence("Home"))
        first_action.triggered.connect(self._first_page)

        last_action = nav_menu.addAction("Last Page")
        last_action.setShortcut(QKeySequence("End"))
        last_action.triggered.connect(self._last_page)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About COMIO")
        about_action.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # Navigation section
        self._btn_library = QToolButton()
        self._btn_library.setText("📚 Library")
        self._btn_library.setCheckable(True)
        self._btn_library.setChecked(True)
        self._btn_library.clicked.connect(lambda: self._switch_view("library"))
        toolbar.addWidget(self._btn_library)

        self._btn_reader = QToolButton()
        self._btn_reader.setText("📖 Reader")
        self._btn_reader.setCheckable(True)
        self._btn_reader.clicked.connect(lambda: self._switch_view("reader"))
        toolbar.addWidget(self._btn_reader)

        self._btn_ia = QToolButton()
        self._btn_ia.setText("🌐 Archive")
        self._btn_ia.setCheckable(True)
        self._btn_ia.clicked.connect(lambda: self._switch_view("ia"))
        toolbar.addWidget(self._btn_ia)

        toolbar.addSeparator()

        # Reader controls (visible when reading)
        self._btn_prev = QToolButton()
        self._btn_prev.setText("◀ Prev")
        self._btn_prev.clicked.connect(self._prev_page)
        toolbar.addWidget(self._btn_prev)

        self._btn_next = QToolButton()
        self._btn_next.setText("Next ▶")
        self._btn_next.clicked.connect(self._next_page)
        toolbar.addWidget(self._btn_next)

        toolbar.addSeparator()

        self._btn_zoom_in = QToolButton()
        self._btn_zoom_in.setText("🔍+")
        self._btn_zoom_in.clicked.connect(lambda: self._viewer.zoom_in())
        toolbar.addWidget(self._btn_zoom_in)

        self._btn_zoom_out = QToolButton()
        self._btn_zoom_out.setText("🔍-")
        self._btn_zoom_out.clicked.connect(lambda: self._viewer.zoom_out())
        toolbar.addWidget(self._btn_zoom_out)

    def _setup_central(self):
        # Main stacked widget
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # 1. Library view
        self._library_view = LibraryView(self._settings)
        self._library_view.comic_opened.connect(self._open_comic)
        self._stack.addWidget(self._library_view)

        # 2. Reader view (viewer + nav bar)
        reader_container = QWidget()
        reader_layout = QVBoxLayout(reader_container)
        reader_layout.setContentsMargins(0, 0, 0, 0)
        reader_layout.setSpacing(0)

        self._viewer = ComicViewer()
        self._viewer.page_changed.connect(self._on_page_changed)
        self._viewer.zoom_changed.connect(self._on_zoom_changed)
        self._viewer.next_page_requested.connect(self._next_page)
        self._viewer.prev_page_requested.connect(self._prev_page)
        reader_layout.addWidget(self._viewer, stretch=1)

        self._nav_bar = PageNavigationBar()
        self._nav_bar.page_requested.connect(self._go_to_page)
        self._nav_bar.fit_mode_requested.connect(self._set_fit_mode)
        self._nav_bar.view_mode_requested.connect(self._set_view_mode)
        self._nav_bar.filter_requested.connect(self._set_reader_filter)
        self._nav_bar.fullscreen_requested.connect(self._toggle_fullscreen)
        self._nav_bar.update_modes(self._settings.fit_mode, self._settings.view_mode, "none")
        reader_layout.addWidget(self._nav_bar)

        self._stack.addWidget(reader_container)

        # 3. Internet Archive browser
        self._ia_panel = IABrowserPanel(self._settings)
        self._ia_panel.download_requested.connect(self._download_ia_comic)
        self._stack.addWidget(self._ia_panel)

        # Start on library
        self._stack.setCurrentIndex(0)

    def _setup_statusbar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        self._status_label = QLabel("Ready")
        status.addWidget(self._status_label, stretch=1)

        self._download_progress = QProgressBar()
        self._download_progress.setFixedWidth(200)
        self._download_progress.setVisible(False)
        status.addPermanentWidget(self._download_progress)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("Space"), self, self._next_page)
        QShortcut(QKeySequence("Backspace"), self, self._prev_page)
        QShortcut(QKeySequence("Ctrl++"), self, lambda: self._viewer.zoom_in())
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self._viewer.zoom_out())
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self._viewer.zoom_reset())
        QShortcut(QKeySequence("Escape"), self, self._escape_handler)

    # ── View Switching ────────────────────────────────────────────────

    def _switch_view(self, view_name: str):
        self._btn_library.setChecked(view_name == "library")
        self._btn_reader.setChecked(view_name == "reader")
        self._btn_ia.setChecked(view_name == "ia")

        if view_name == "library":
            self._stack.setCurrentIndex(0)
        elif view_name == "reader":
            self._stack.setCurrentIndex(1)
        elif view_name == "ia":
            self._stack.setCurrentIndex(2)

    # ── File Operations ───────────────────────────────────────────────

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Comic",
            "",
            "Comic Books (*.cbz *.cbr *.zip *.rar);;All Files (*)"
        )
        if file_path:
            self._open_comic(file_path)

    def _open_comic(self, file_path: str):
        """Open a comic file for reading."""
        try:
            # Close current comic
            if self._current_comic:
                self._current_comic.close()

            self._current_comic = ComicBook(file_path)
            self._viewer.total_pages = self._current_comic.page_count
            self._viewer.clear_cache()

            # Restore preferred fit and view modes from settings
            self._viewer.view_mode = self._settings.view_mode
            self._viewer.fit_mode = self._settings.fit_mode
            self._nav_bar.update_modes(self._viewer.fit_mode, self._viewer.view_mode, self._viewer.reader_filter)

            # Check for manga mode
            if self._current_comic.metadata.is_manga:
                self._viewer.reading_direction = "rtl"

            # Load bookmark or start at page 0
            bookmark = self._settings.get_bookmark(file_path)
            self._go_to_page(bookmark)

            # Switch to reader
            self._switch_view("reader")

            # Update title and history
            self.setWindowTitle(f"COMIO — {self._current_comic.metadata.display_title}")
            self._settings.last_opened_file = file_path
            self._settings.add_recent_file(file_path)

            self._status_label.setText(
                f"📖 {self._current_comic.metadata.display_title} — "
                f"{self._current_comic.page_count} pages"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open comic:\n{e}")

    # ── Page Navigation ───────────────────────────────────────────────

    def _go_to_page(self, page_index: int):
        """Navigate to a specific page."""
        if not self._current_comic:
            return

        page_index = max(0, min(page_index, self._current_comic.page_count - 1))

        if self._viewer.view_mode == ComicViewer.MODE_DOUBLE:
            self._display_double_page(page_index)
        else:
            self._display_single_page(page_index)

        # Preload adjacent pages
        for i in range(1, 4):
            next_path = self._current_comic.get_page_path(page_index + i)
            if next_path:
                self._viewer.preload_page(page_index + i, next_path)

        # Save bookmark
        self._settings.set_bookmark(self._current_comic.file_path, page_index)

    def _display_single_page(self, index: int):
        """Display a single page."""
        # Check cache first
        cached = self._viewer.get_cached_page(index)
        if cached:
            self._viewer.display_page(cached, index)
        else:
            page_path = self._current_comic.get_page_path(index)
            if page_path:
                pixmap = QPixmap(page_path)
                if not pixmap.isNull():
                    self._viewer.display_page(pixmap, index)

        self._nav_bar.update_page(index, self._current_comic.page_count)

    def _display_double_page(self, index: int):
        """Display two pages side by side."""
        left_path = self._current_comic.get_page_path(index)
        right_index = index + 1
        right_path = self._current_comic.get_page_path(right_index)

        if left_path and right_path:
            left_pix = QPixmap(left_path)
            right_pix = QPixmap(right_path)
            if not left_pix.isNull() and not right_pix.isNull():
                self._viewer.display_double_page(left_pix, right_pix, index, right_index)
        elif left_path:
            pixmap = QPixmap(left_path)
            if not pixmap.isNull():
                self._viewer.display_page(pixmap, index)

        self._nav_bar.update_page(index, self._current_comic.page_count)

    def _next_page(self):
        if not self._current_comic:
            return
        step = 2 if self._viewer.view_mode == ComicViewer.MODE_DOUBLE else 1
        new_page = self._viewer.current_page + step
        if new_page < self._current_comic.page_count:
            self._go_to_page(new_page)

    def _prev_page(self):
        if not self._current_comic:
            return
        step = 2 if self._viewer.view_mode == ComicViewer.MODE_DOUBLE else 1
        new_page = self._viewer.current_page - step
        if new_page >= 0:
            self._go_to_page(new_page)

    def _first_page(self):
        self._go_to_page(0)

    def _last_page(self):
        if self._current_comic:
            self._go_to_page(self._current_comic.page_count - 1)

    # ── View Mode ─────────────────────────────────────────────────────

    def _set_view_mode(self, mode: str):
        self._viewer.view_mode = mode
        self._settings.view_mode = mode
        self._nav_bar.update_modes(self._viewer.fit_mode, self._viewer.view_mode, self._viewer.reader_filter)
        if self._current_comic:
            self._go_to_page(self._viewer.current_page)

    def _set_fit_mode(self, mode: str):
        self._viewer.fit_mode = mode
        self._settings.fit_mode = mode
        self._nav_bar.update_modes(self._viewer.fit_mode, self._viewer.view_mode, self._viewer.reader_filter)

    def _set_reader_filter(self, filter_mode: str):
        self._viewer.reader_filter = filter_mode
        self._nav_bar.update_modes(self._viewer.fit_mode, self._viewer.view_mode, filter_mode)

    # ── Theme ─────────────────────────────────────────────────────────

    def _set_theme(self, theme: str):
        self._settings.theme = theme
        self.setStyleSheet(get_theme(theme))

    # ── Fullscreen ────────────────────────────────────────────────────

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().show()
            self.statusBar().show()
            self._fullscreen_action.setChecked(False)
        else:
            self.menuBar().hide()
            self.statusBar().hide()
            self.showFullScreen()
            self._fullscreen_action.setChecked(True)

    def _escape_handler(self):
        if self.isFullScreen():
            self._toggle_fullscreen()
        elif self._stack.currentIndex() == 1:  # Reader
            self._switch_view("library")

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_page_changed(self, page: int):
        if self._current_comic:
            self._nav_bar.update_page(page, self._current_comic.page_count)

    def _on_zoom_changed(self, zoom: float):
        self._nav_bar.update_zoom(zoom)

    # ── Internet Archive ──────────────────────────────────────────────

    def _download_ia_comic(self, comic: IAComic):
        """Download a comic from Internet Archive."""
        best = comic.get_best_download()
        if not best:
            return

        url = comic.get_download_url(best["name"])
        filename = best["name"]

        task = self._download_manager.add_download(
            url=url,
            filename=filename,
            destination=self._settings.download_path,
            identifier=comic.identifier,
            title=comic.title,
        )

        self._download_progress.setVisible(True)
        self._download_progress.setValue(0)
        self._status_label.setText(f"⬇️ Downloading: {comic.title}")



    def _on_download_progress(self, task):
        self._download_progress.setValue(int(task.progress))
        self._status_label.setText(
            f"⬇️ {task.title} — {task.progress:.0f}% ({task.speed_display})"
        )

    def _on_download_completed(self, task):
        self._download_progress.setVisible(False)
        self._status_label.setText(f"✅ Downloaded: {task.title}")

        # Refresh library
        QTimer.singleShot(500, self._library_view.scan_library)

    def _on_download_failed(self, task):
        self._download_progress.setVisible(False)
        self._status_label.setText(f"❌ Download failed: {task.title} — {task.error}")

    # ── About ─────────────────────────────────────────────────────────

    def _show_about(self):
        QMessageBox.about(
            self,
            "About COMIO",
            "<h2 style='color: #F97316;'>COMIO</h2>"
            "<p><b>The Comic Reader That Sets Your Collection Free</b></p>"
            "<p>Version 1.0.0</p>"
            "<p>• Read CBZ, CBR comic files<br>"
            "• Browse & download free comics from Internet Archive<br>"
            "• Fullscreen, zoom, double-page spread<br>"
            "• Dark & light themes</p>"
            "<p style='color: #888;'>Powered by Internet Archive</p>"
        )

    # ── Window Events ─────────────────────────────────────────────────

    def closeEvent(self, event):
        """Save state on close."""
        self._settings.window_geometry = self.saveGeometry()
        self._settings.window_state = self.saveState()

        if self._current_comic:
            self._current_comic.close()

        self._viewer.cleanup()
        self._download_manager.cancel_all()

        event.accept()

"""
COMIO — Library Manager
Grid view for browsing, importing, and managing the comic collection.
"""

import os
import json
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QFrame, QMenu, QFileDialog, QSizePolicy,
    QMessageBox, QApplication
)
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont,
    QDragEnterEvent, QDropEvent, QMouseEvent, QAction
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QTimer, QThread
)
from PIL import Image

from comic_loader import ComicBook
from metadata import ComicMetadata


COMIC_EXTENSIONS = {".cbz", ".cbr", ".zip", ".rar"}
THUMBNAIL_SIZE = (180, 260)


class ThumbnailGenerator(QThread):
    """Background thread for generating comic thumbnails."""
    thumbnail_ready = pyqtSignal(str, QPixmap)  # file_path, thumbnail

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: list[tuple[str, str]] = []  # (comic_path, thumb_path)

    def add(self, comic_path: str, thumb_path: str):
        self._queue.append((comic_path, thumb_path))
        if not self.isRunning():
            self.start()

    def run(self):
        while self._queue:
            comic_path, thumb_path = self._queue.pop(0)
            try:
                # Extract cover from comic
                comic = ComicBook(comic_path)
                cover_path = comic.get_cover_path()

                if cover_path and os.path.exists(cover_path):
                    # Generate thumbnail with Pillow
                    img = Image.open(cover_path)
                    img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

                    # Save thumbnail
                    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                    img.save(thumb_path, "JPEG", quality=85)

                    # Emit as QPixmap
                    pixmap = QPixmap(thumb_path)
                    if not pixmap.isNull():
                        self.thumbnail_ready.emit(comic_path, pixmap)

                comic.close()

            except Exception as e:
                print(f"Thumbnail generation failed for {comic_path}: {e}")


class ComicCard(QFrame):
    """A single comic card in the library grid."""
    clicked = pyqtSignal(str)  # file_path
    double_clicked = pyqtSignal(str)  # file_path
    context_menu_requested = pyqtSignal(str, object)  # file_path, QPoint

    def __init__(self, file_path: str, metadata: ComicMetadata, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.metadata = metadata
        self._selected = False

        self.setFixedSize(200, 310)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("comicCard")
        self.setStyleSheet("""
            #comicCard {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 2px solid transparent;
            }
            #comicCard:hover {
                border-color: #F97316;
                background-color: #1f1f1f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Cover image
        self._cover_label = QLabel()
        self._cover_label.setFixedSize(184, 250)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setStyleSheet("""
            background-color: #111111;
            border-radius: 8px;
            color: #444;
            font-size: 11px;
        """)
        self._cover_label.setText("Loading...")
        layout.addWidget(self._cover_label)

        # Title
        title_text = metadata.display_title
        if len(title_text) > 25:
            title_text = title_text[:22] + "..."
        self._title_label = QLabel(title_text)
        self._title_label.setStyleSheet("""
            color: #e0e0e0;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setToolTip(metadata.display_title)
        layout.addWidget(self._title_label)

    def set_thumbnail(self, pixmap: QPixmap):
        """Set the cover thumbnail."""
        scaled = pixmap.scaled(
            184, 250,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._cover_label.setPixmap(scaled)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet("""
                #comicCard {
                    background-color: #1f1f1f;
                    border-radius: 12px;
                    border: 2px solid #F97316;
                }
            """)
        else:
            self.setStyleSheet("""
                #comicCard {
                    background-color: #1a1a1a;
                    border-radius: 12px;
                    border: 2px solid transparent;
                }
                #comicCard:hover {
                    border-color: #F97316;
                    background-color: #1f1f1f;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.file_path)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(self.file_path, event.globalPos())


class LibraryView(QWidget):
    """
    Main library view showing a grid of comic cards.
    
    Signals:
        comic_opened(str): Emitted when a comic is opened for reading.
    """
    comic_opened = pyqtSignal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._cards: dict[str, ComicCard] = {}  # file_path -> card
        self._metadata_cache: dict[str, ComicMetadata] = {}
        self._selected_path: Optional[str] = None

        # Background thumbnail generator
        self._thumb_gen = ThumbnailGenerator(self)
        self._thumb_gen.thumbnail_ready.connect(self._on_thumbnail_ready)

        self._setup_ui()
        
        # Enable drag and drop
        self.setAcceptDrops(True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ──
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet("background-color: #111111; border-bottom: 1px solid #1a1a1a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)

        # Title
        title = QLabel("📚 Library")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #F97316; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Search bar
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Search comics...")
        self._search_input.setFixedWidth(250)
        self._search_input.textChanged.connect(self._filter_cards)
        header_layout.addWidget(self._search_input)

        # Import button
        import_btn = QPushButton("+ Import")
        import_btn.setFixedSize(90, 34)
        import_btn.clicked.connect(self._import_comics)
        header_layout.addWidget(import_btn)

        layout.addWidget(header)

        # ── Scroll area with grid ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0d0d0d; }")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background-color: #0d0d0d;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(20, 20, 20, 20)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll)

        # ── Empty state ──
        self._empty_label = QLabel("No comics yet\n\nDrag & drop CBZ/CBR files here\nor click Import to add comics")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("""
            color: #555;
            font-size: 16px;
            padding: 60px;
            background: transparent;
        """)

    def scan_library(self):
        """Scan the library directory for comic files."""
        library_path = self._settings.library_path
        if not os.path.exists(library_path):
            os.makedirs(library_path, exist_ok=True)
            return

        comic_files = []
        for root, dirs, files in os.walk(library_path):
            for filename in files:
                if Path(filename).suffix.lower() in COMIC_EXTENSIONS:
                    comic_files.append(os.path.join(root, filename))

        for file_path in sorted(comic_files):
            self._add_comic_card(file_path)

        self._update_empty_state()

    def _add_comic_card(self, file_path: str):
        """Add a comic card to the grid."""
        if file_path in self._cards:
            return

        # Get or create metadata
        metadata = self._get_metadata(file_path)

        # Create card
        card = ComicCard(file_path, metadata)
        card.clicked.connect(self._on_card_clicked)
        card.double_clicked.connect(self._on_card_double_clicked)
        card.context_menu_requested.connect(self._on_context_menu)

        self._cards[file_path] = card

        # Add to grid
        count = len(self._cards) - 1
        cols = max(1, (self.width() - 40) // 216)  # 200 + 16 spacing
        row = count // cols
        col = count % cols
        self._grid_layout.addWidget(card, row, col)

        # Queue thumbnail generation
        thumb_dir = os.path.join(self._settings.library_path, ".thumbnails")
        safe_name = Path(file_path).stem.replace(" ", "_")[:50]
        thumb_path = os.path.join(thumb_dir, f"{safe_name}.jpg")

        if os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            if not pixmap.isNull():
                card.set_thumbnail(pixmap)
        else:
            self._thumb_gen.add(file_path, thumb_path)

    def _get_metadata(self, file_path: str) -> ComicMetadata:
        """Get metadata for a comic file."""
        if file_path in self._metadata_cache:
            return self._metadata_cache[file_path]

        try:
            comic = ComicBook(file_path)
            metadata = comic.metadata
            comic.close()
        except Exception:
            metadata = ComicMetadata(
                title=Path(file_path).stem,
                file_path=file_path,
            )

        self._metadata_cache[file_path] = metadata
        return metadata

    def _on_thumbnail_ready(self, file_path: str, pixmap: QPixmap):
        """Handle a thumbnail ready from the background generator."""
        card = self._cards.get(file_path)
        if card:
            card.set_thumbnail(pixmap)

    def _on_card_clicked(self, file_path: str):
        # Deselect previous
        if self._selected_path and self._selected_path in self._cards:
            self._cards[self._selected_path].set_selected(False)
        # Select new
        self._selected_path = file_path
        self._cards[file_path].set_selected(True)

    def _on_card_double_clicked(self, file_path: str):
        """Open a comic for reading."""
        self.comic_opened.emit(file_path)

    def _on_context_menu(self, file_path: str, pos):
        """Show context menu for a comic card."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F97316;
                color: white;
            }
        """)

        open_action = menu.addAction("📖 Open")
        open_action.triggered.connect(lambda: self.comic_opened.emit(file_path))

        menu.addSeparator()

        info_action = menu.addAction("ℹ️ Info")
        info_action.triggered.connect(lambda: self._show_info(file_path))

        menu.addSeparator()

        remove_action = menu.addAction("🗑️ Remove from Library")
        remove_action.triggered.connect(lambda: self._remove_comic(file_path))

        menu.exec(pos)

    def _show_info(self, file_path: str):
        """Show comic info dialog."""
        meta = self._get_metadata(file_path)
        info_text = (
            f"Title: {meta.display_title}\n"
            f"Series: {meta.series}\n"
            f"Number: {meta.number}\n"
            f"Writer: {meta.writer}\n"
            f"Pages: {meta.page_count}\n"
            f"Publisher: {meta.publisher}\n"
            f"Year: {meta.year or 'Unknown'}\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Size: {os.path.getsize(file_path) / (1024*1024):.1f} MB"
        )
        QMessageBox.information(self, "Comic Info", info_text)

    def _remove_comic(self, file_path: str):
        """Remove a comic from the library view."""
        card = self._cards.pop(file_path, None)
        if card:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._metadata_cache.pop(file_path, None)
        self._relayout_grid()
        self._update_empty_state()

    def _relayout_grid(self):
        """Re-layout the grid after removal."""
        cards = list(self._cards.values())
        cols = max(1, (self.width() - 40) // 216)
        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(card, row, col)

    def _filter_cards(self, text: str):
        """Filter cards by search text."""
        text = text.lower()
        for path, card in self._cards.items():
            matches = (
                text in card.metadata.display_title.lower() or
                text in card.metadata.writer.lower() or
                text in card.metadata.publisher.lower() or
                text in os.path.basename(path).lower()
            )
            card.setVisible(matches)

    def _import_comics(self):
        """Open file dialog to import comics."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Comics",
            "",
            "Comic Books (*.cbz *.cbr *.zip *.rar);;All Files (*)"
        )
        if files:
            self._import_files(files)

    def _import_files(self, file_paths: list[str]):
        """Import comic files into the library."""
        library_path = self._settings.library_path
        os.makedirs(library_path, exist_ok=True)
        
        lib_path_norm = os.path.normpath(library_path).lower()

        for src in file_paths:
            try:
                src_norm = os.path.normpath(src).lower()
                if not src_norm.startswith(lib_path_norm):
                    import shutil
                    dst = os.path.join(library_path, os.path.basename(src))
                    # Prevent copying same file
                    if os.path.normpath(dst).lower() != src_norm:
                        if not os.path.exists(dst):
                            shutil.copy2(src, dst)
                        self._add_comic_card(dst)
                    else:
                        self._add_comic_card(src)
                else:
                    self._add_comic_card(src)
            except Exception as e:
                print(f"Failed to import file {src}: {e}")
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to import comic:\n{os.path.basename(src)}\n\nError: {e}"
                )

        self._update_empty_state()

    def _update_empty_state(self):
        """Show/hide empty state label."""
        if not self._cards:
            if self._empty_label.parent() is None:
                self._grid_layout.addWidget(
                    self._empty_label, 0, 0, 1, 4,
                    Qt.AlignmentFlag.AlignCenter
                )
            self._empty_label.show()
        else:
            self._empty_label.hide()

    # ── Drag & Drop ───────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in COMIC_EXTENSIONS:
                files.append(path)
        if files:
            self._import_files(files)
            event.acceptProposedAction()

    def resizeEvent(self, event):
        """Re-layout grid on resize."""
        super().resizeEvent(event)
        QTimer.singleShot(100, self._relayout_grid)

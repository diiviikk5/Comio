"""
COMIO — Comic Page Viewer
QGraphicsView-based image viewer with zoom, pan, page navigation,
fit modes, double-page spread, and fullscreen support.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QSizePolicy, QPushButton, QFrame, QButtonGroup,
    QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QPixmap, QImage, QWheelEvent, QKeyEvent,
    QPainter, QColor, QMouseEvent, QResizeEvent
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QTimer, QThread, pyqtSlot, QPropertyAnimation
from PIL import Image


class PageLoaderThread(QThread):
    """Background thread for loading/preloading pages."""
    page_loaded = pyqtSignal(int, QPixmap)  # page_index, pixmap

    def __init__(self, parent=None):
        super().__init__(parent)
        self._requests: list[tuple[int, str]] = []
        self._running = True

    def add_request(self, page_index: int, file_path: str):
        self._requests.append((page_index, file_path))
        if not self.isRunning():
            self.start()

    def run(self):
        while self._requests:
            page_index, file_path = self._requests.pop(0)
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.page_loaded.emit(page_index, pixmap)
            except Exception:
                pass

    def stop(self):
        self._running = False
        self._requests.clear()


class ComicViewer(QGraphicsView):
    """
    High-performance comic page viewer.
    
    Signals:
        page_changed(int): Emitted when the current page changes.
        zoom_changed(float): Emitted when zoom level changes.
        view_mode_changed(str): Emitted when view mode changes.
    """
    
    page_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(float)
    view_mode_changed = pyqtSignal(str)
    next_page_requested = pyqtSignal()
    prev_page_requested = pyqtSignal()

    # View modes
    MODE_SINGLE = "single"
    MODE_DOUBLE = "double"
    MODE_VERTICAL = "vertical"

    # Fit modes
    FIT_WIDTH = "width"
    FIT_HEIGHT = "height"
    FIT_PAGE = "page"
    FIT_ORIGINAL = "original"
    FIT_AUTO = "auto"

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self._current_page = 0
        self._total_pages = 0
        self._zoom_factor = 1.0
        self._view_mode = self.MODE_SINGLE
        self._fit_mode = self.FIT_WIDTH
        self._reading_direction = "ltr"  # or "rtl"
        self._is_fullscreen = False
        self._reader_filter = "none"  # "none", "sepia", "warm", "dim"

        # Page cache
        self._page_cache: dict[int, QPixmap] = {}
        self._max_cache_size = 20

        # Setup scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._current_item: Optional[QGraphicsPixmapItem] = None
        self._second_item: Optional[QGraphicsPixmapItem] = None  # For double page

        # Background loader
        self._loader = PageLoaderThread(self)
        self._loader.page_loaded.connect(self._on_page_preloaded)

        # Configure view
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QColor("#0a0a0a"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Gesture tracking
        self._pan_start = None
        self._is_panning = False

    # ── Page Display ──────────────────────────────────────────────────

    def display_page(self, pixmap: QPixmap, page_index: int):
        """Display a single page with transition."""
        self._scene.clear()
        self._second_item = None
        self._current_item = self._scene.addPixmap(pixmap)
        self._current_page = page_index
        self._page_cache[page_index] = pixmap
        self._trim_cache()
        self._apply_fit_mode()
        self._animate_fade_in()
        self.page_changed.emit(page_index)

    def display_double_page(self, left_pixmap: QPixmap, right_pixmap: QPixmap,
                             left_index: int, right_index: int):
        """Display two pages side by side with transition."""
        self._scene.clear()

        # For RTL reading, swap the pages
        if self._reading_direction == "rtl":
            left_pixmap, right_pixmap = right_pixmap, left_pixmap

        self._current_item = self._scene.addPixmap(left_pixmap)
        self._second_item = self._scene.addPixmap(right_pixmap)

        # Position second page next to first with a small gap
        gap = 4
        self._second_item.setPos(left_pixmap.width() + gap, 0)

        self._current_page = min(left_index, right_index)
        self._page_cache[left_index] = left_pixmap
        self._page_cache[right_index] = right_pixmap
        self._trim_cache()
        self._apply_fit_mode()
        self._animate_fade_in()
        self.page_changed.emit(self._current_page)

    def _animate_fade_in(self):
        """Smoothly fade in the displayed page(s) over 180ms."""
        if not self._current_item:
            return
            
        self._opacity_effect_1 = QGraphicsOpacityEffect()
        self._current_item.setGraphicsEffect(self._opacity_effect_1)
        
        self._anim_1 = QPropertyAnimation(self._opacity_effect_1, b"opacity")
        self._anim_1.setDuration(180)
        self._anim_1.setStartValue(0.0)
        self._anim_1.setEndValue(1.0)
        self._anim_1.start()
        
        if self._second_item:
            self._opacity_effect_2 = QGraphicsOpacityEffect()
            self._second_item.setGraphicsEffect(self._opacity_effect_2)
            
            self._anim_2 = QPropertyAnimation(self._opacity_effect_2, b"opacity")
            self._anim_2.setDuration(180)
            self._anim_2.setStartValue(0.0)
            self._anim_2.setEndValue(1.0)
            self._anim_2.start()

    @property
    def reader_filter(self) -> str:
        return self._reader_filter

    @reader_filter.setter
    def reader_filter(self, value: str):
        if value in ("none", "sepia", "warm", "dim"):
            self._reader_filter = value
            self.viewport().update()  # Repaint viewport with new color filter

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """Draw active eye-care color filters over the reading viewport."""
        super().drawForeground(painter, rect)
        
        if self._reader_filter == "sepia":
            painter.fillRect(rect, QColor(230, 194, 128, 30))  # ~12% opacity sepia
        elif self._reader_filter == "warm":
            painter.fillRect(rect, QColor(255, 153, 51, 25))   # ~10% opacity warm amber
        elif self._reader_filter == "dim":
            painter.fillRect(rect, QColor(0, 0, 0, 50))        # ~20% opacity dimming overlay

    def _apply_fit_mode(self):
        """Apply the current fit mode to the displayed content."""
        if not self._current_item:
            return

        scene_rect = self._scene.itemsBoundingRect()
        
        if self._fit_mode == self.FIT_WIDTH:
            # Fit to viewport width
            viewport_width = self.viewport().width() - 20
            scale = viewport_width / scene_rect.width() if scene_rect.width() > 0 else 1
            self.resetTransform()
            self.scale(scale, scale)
            self._zoom_factor = scale
            
        elif self._fit_mode == self.FIT_HEIGHT:
            viewport_height = self.viewport().height() - 20
            scale = viewport_height / scene_rect.height() if scene_rect.height() > 0 else 1
            self.resetTransform()
            self.scale(scale, scale)
            self._zoom_factor = scale
            
        elif self._fit_mode == self.FIT_PAGE:
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_factor = self.transform().m11()
            
        elif self._fit_mode == self.FIT_AUTO:
            viewport_w = self.viewport().width() - 4
            viewport_h = self.viewport().height() - 4
            page_w = scene_rect.width()
            page_h = scene_rect.height()
            
            if page_w > 0 and page_h > 0:
                if page_w / page_h > 1.2:
                    scale = viewport_w / page_w
                else:
                    scale = viewport_h / page_h
                self.resetTransform()
                self.scale(scale, scale)
                self._zoom_factor = scale
            
        elif self._fit_mode == self.FIT_ORIGINAL:
            self.resetTransform()
            self._zoom_factor = 1.0

        self.zoom_changed.emit(self._zoom_factor)

    # ── Zoom ──────────────────────────────────────────────────────────

    def zoom_in(self, factor: float = 1.15):
        """Zoom in by the given factor."""
        self._zoom_factor *= factor
        self.scale(factor, factor)
        self._fit_mode = self.FIT_ORIGINAL  # Exit fit mode on manual zoom
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_out(self, factor: float = 1.15):
        """Zoom out by the given factor."""
        self._zoom_factor /= factor
        self.scale(1 / factor, 1 / factor)
        self._fit_mode = self.FIT_ORIGINAL
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_reset(self):
        """Reset to 100% zoom."""
        self.resetTransform()
        self._zoom_factor = 1.0
        self._fit_mode = self.FIT_ORIGINAL
        self.zoom_changed.emit(self._zoom_factor)

    # ── Navigation ────────────────────────────────────────────────────

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def total_pages(self) -> int:
        return self._total_pages

    @total_pages.setter
    def total_pages(self, value: int):
        self._total_pages = value

    def can_go_next(self) -> bool:
        step = 2 if self._view_mode == self.MODE_DOUBLE else 1
        return self._current_page + step < self._total_pages

    def can_go_prev(self) -> bool:
        return self._current_page > 0

    # ── View Mode ─────────────────────────────────────────────────────

    @property
    def view_mode(self) -> str:
        return self._view_mode

    @view_mode.setter
    def view_mode(self, mode: str):
        self._view_mode = mode
        self.view_mode_changed.emit(mode)

    @property
    def fit_mode(self) -> str:
        return self._fit_mode

    @fit_mode.setter
    def fit_mode(self, mode: str):
        self._fit_mode = mode
        self._apply_fit_mode()

    @property
    def reading_direction(self) -> str:
        return self._reading_direction

    @reading_direction.setter
    def reading_direction(self, direction: str):
        self._reading_direction = direction

    # ── Cache ─────────────────────────────────────────────────────────

    def get_cached_page(self, index: int) -> Optional[QPixmap]:
        return self._page_cache.get(index)

    def cache_page(self, index: int, pixmap: QPixmap):
        self._page_cache[index] = pixmap
        self._trim_cache()

    def _trim_cache(self):
        """Remove oldest cached pages if over limit."""
        while len(self._page_cache) > self._max_cache_size:
            # Remove the page furthest from current
            farthest = max(
                self._page_cache.keys(),
                key=lambda k: abs(k - self._current_page)
            )
            del self._page_cache[farthest]

    def clear_cache(self):
        self._page_cache.clear()

    # ── Preloading ────────────────────────────────────────────────────

    @pyqtSlot(int, QPixmap)
    def _on_page_preloaded(self, index: int, pixmap: QPixmap):
        """Handle a preloaded page from the background thread."""
        self._page_cache[index] = pixmap
        self._trim_cache()

    def preload_page(self, index: int, file_path: str):
        """Queue a page for background loading."""
        if index not in self._page_cache:
            self._loader.add_request(index, file_path)

    # ── Events ────────────────────────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent):
        """Handle scroll wheel for zoom (Ctrl) or page navigation."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in(1.1)
            elif delta < 0:
                self.zoom_out(1.1)
            event.accept()
        else:
            # Check scroll boundaries for page changes
            v_bar = self.verticalScrollBar()
            delta = event.angleDelta().y()
            
            if not v_bar.isVisible() or v_bar.maximum() == 0:
                # Page fits fully in viewport, direct scroll turns pages
                if delta < -40:
                    self.next_page_requested.emit()
                elif delta > 40:
                    self.prev_page_requested.emit()
                event.accept()
            else:
                val = v_bar.value()
                max_val = v_bar.maximum()
                if val >= max_val - 2 and delta < -40:
                    self.next_page_requested.emit()
                    event.accept()
                elif val <= 2 and delta > 40:
                    self.prev_page_requested.emit()
                    event.accept()
                else:
                    super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        """Re-apply fit mode when the view is resized."""
        super().resizeEvent(event)
        if self._fit_mode != self.FIT_ORIGINAL:
            QTimer.singleShot(50, self._apply_fit_mode)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Toggle fullscreen on double-click."""
        window = self.window()
        if window:
            if window.isFullScreen():
                window.showNormal()
            else:
                window.showFullScreen()
        event.accept()

    # ── Cleanup ───────────────────────────────────────────────────────

    def cleanup(self):
        """Stop background tasks and clear cache."""
        self._loader.stop()
        if self._loader.isRunning():
            self._loader.wait(1000)
        self.clear_cache()
        self._scene.clear()


class PageNavigationBar(QWidget):
    """
    Premium reader control bar showing page info, fitting controls, view modes, filters, and zoom.
    """
    page_requested = pyqtSignal(int)
    fit_mode_requested = pyqtSignal(str)
    view_mode_requested = pyqtSignal(str)
    filter_requested = pyqtSignal(str)
    fullscreen_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #111111;
                border-top: 1px solid #1c1c1c;
            }
            QLabel {
                color: #a0a0a0;
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #262626;
                border-radius: 2px;
                border: none;
            }
            QSlider::sub-page:horizontal {
                background: #F97316;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FB923C;
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #F97316;
            }
            QFrame#controlGroup {
                background-color: #161616;
                border: 1px solid #222222;
                border-radius: 6px;
                padding: 1px;
            }
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #e0e0e0;
                background-color: #222222;
            }
            QPushButton:checked {
                background-color: #262626;
                color: #F97316;
                font-weight: 700;
            }
            QPushButton#actionBtn {
                background-color: #161616;
                color: #a0a0a0;
                border: 1px solid #222222;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton#actionBtn:hover {
                border-color: #F97316;
                color: white;
                background-color: #1c1c1c;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(16)
        
        # 1. Page Info
        self._page_label = QLabel("Page 0 / 0")
        self._page_label.setFixedWidth(85)
        layout.addWidget(self._page_label)
        
        # 2. Page Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider, stretch=1)
        
        # 3. Zoom Display
        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(40)
        layout.addWidget(self._zoom_label)
        
        # 4. Fit Mode Group (Segmented Control)
        fit_group = QFrame()
        fit_group.setObjectName("controlGroup")
        fit_layout = QHBoxLayout(fit_group)
        fit_layout.setContentsMargins(0, 0, 0, 0)
        fit_layout.setSpacing(0)
        
        self._fit_buttons = {}
        modes = [("Auto", "auto"), ("Page", "page"), ("Width", "width"), ("Height", "height")]
        from PyQt6.QtWidgets import QButtonGroup
        self._fit_btn_group = QButtonGroup(self)
        self._fit_btn_group.setExclusive(True)
        
        for label, code in modes:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=code: self.fit_mode_requested.emit(c))
            self._fit_btn_group.addButton(btn)
            fit_layout.addWidget(btn)
            self._fit_buttons[code] = btn
            
        self._fit_buttons["width"].setChecked(True)  # default
        layout.addWidget(fit_group)
        
        # 5. View Mode Group (Segmented Control)
        view_group = QFrame()
        view_group.setObjectName("controlGroup")
        view_layout = QHBoxLayout(view_group)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(0)
        
        self._view_buttons = {}
        v_modes = [("Single", "single"), ("Double", "double")]
        self._view_btn_group = QButtonGroup(self)
        self._view_btn_group.setExclusive(True)
        
        for label, code in v_modes:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=code: self.view_mode_requested.emit(c))
            self._view_btn_group.addButton(btn)
            view_layout.addWidget(btn)
            self._view_buttons[code] = btn
            
        self._view_buttons["single"].setChecked(True)
        layout.addWidget(view_group)
        
        # 6. Eye-Care Filter Group (Segmented Control)
        filter_group = QFrame()
        filter_group.setObjectName("controlGroup")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(0)
        
        self._filter_buttons = {}
        filters_list = [("Normal", "none"), ("Sepia", "sepia"), ("Warm", "warm"), ("Dim", "dim")]
        self._filter_btn_group = QButtonGroup(self)
        self._filter_btn_group.setExclusive(True)
        
        for label, code in filters_list:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=code: self.filter_requested.emit(c))
            self._filter_btn_group.addButton(btn)
            filter_layout.addWidget(btn)
            self._filter_buttons[code] = btn
            
        self._filter_buttons["none"].setChecked(True)
        layout.addWidget(filter_group)
        
        # 7. Fullscreen Action Button
        self._fs_btn = QPushButton("📺 Fullscreen")
        self._fs_btn.setObjectName("actionBtn")
        self._fs_btn.clicked.connect(self.fullscreen_requested.emit)
        layout.addWidget(self._fs_btn)
        
    def update_page(self, current: int, total: int):
        """Update the page display."""
        self._page_label.setText(f"Page {current + 1} / {total}")
        self._slider.blockSignals(True)
        self._slider.setMaximum(max(0, total - 1))
        self._slider.setValue(current)
        self._slider.blockSignals(False)
        
    def update_zoom(self, zoom: float):
        """Update the zoom display."""
        self._zoom_label.setText(f"{zoom * 100:.0f}%")
        
    def update_modes(self, fit_mode: str, view_mode: str, filter_mode: str = "none"):
        """Sync active buttons in Segmented controls with current state."""
        btn_fit = self._fit_buttons.get(fit_mode)
        if btn_fit:
            btn_fit.blockSignals(True)
            btn_fit.setChecked(True)
            btn_fit.blockSignals(False)
            
        btn_view = self._view_buttons.get(view_mode)
        if btn_view:
            btn_view.blockSignals(True)
            btn_view.setChecked(True)
            btn_view.blockSignals(False)
            
        btn_filter = self._filter_buttons.get(filter_mode)
        if btn_filter:
            btn_filter.blockSignals(True)
            btn_filter.setChecked(True)
            btn_filter.blockSignals(False)
            
    def _on_slider_changed(self, value: int):
        self.page_requested.emit(value)

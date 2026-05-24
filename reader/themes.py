"""
COMIO Desktop Comic Reader — Dark & Light QSS Themes
"""

DARK_THEME = """
/* ===== COMIO Dark Theme ===== */

/* Global */
QWidget {
    background-color: #0d0d0d;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background-color: #0d0d0d;
}

QMainWindow::separator {
    background-color: #1a1a1a;
    width: 2px;
    height: 2px;
}

/* Menu Bar */
QMenuBar {
    background-color: #111111;
    color: #e0e0e0;
    border-bottom: 1px solid #222222;
    padding: 2px;
}

QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #F97316;
    color: #ffffff;
}

QMenu {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #F97316;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #333333;
    margin: 4px 8px;
}

/* Toolbar */
QToolBar {
    background-color: #111111;
    border: none;
    border-bottom: 1px solid #1a1a1a;
    padding: 4px 8px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QToolButton:hover {
    background-color: #262626;
    color: #F97316;
}

QToolButton:pressed {
    background-color: #333333;
}

QToolButton:checked {
    background-color: #F97316;
    color: #ffffff;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #0d0d0d;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #F97316;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0d0d0d;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #333333;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #F97316;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Status Bar */
QStatusBar {
    background-color: #111111;
    color: #888888;
    border-top: 1px solid #1a1a1a;
    font-size: 12px;
    padding: 2px 8px;
}

/* Labels */
QLabel {
    color: #e0e0e0;
    background: transparent;
}

/* Line Edit / Search */
QLineEdit {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #F97316;
}

QLineEdit:focus {
    border-color: #F97316;
}

QLineEdit::placeholder {
    color: #666666;
}

/* Push Buttons */
QPushButton {
    background-color: #F97316;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #FB923C;
}

QPushButton:pressed {
    background-color: #EA580C;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QPushButton#secondaryButton {
    background-color: transparent;
    color: #e0e0e0;
    border: 1px solid #333333;
}

QPushButton#secondaryButton:hover {
    border-color: #F97316;
    color: #F97316;
}

/* Tab Widget */
QTabWidget::pane {
    background-color: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #111111;
    color: #888888;
    border: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background-color: #0d0d0d;
    color: #F97316;
    border-bottom: 2px solid #F97316;
}

QTabBar::tab:hover {
    color: #e0e0e0;
}

/* Progress Bar */
QProgressBar {
    background-color: #1a1a1a;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #F97316, stop:1 #FB923C);
    border-radius: 6px;
}

/* List Widget (Library) */
QListWidget {
    background-color: #0d0d0d;
    color: #e0e0e0;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-radius: 8px;
    margin: 2px 4px;
}

QListWidget::item:selected {
    background-color: #1a1a1a;
    border: 1px solid #F97316;
}

QListWidget::item:hover {
    background-color: #151515;
}

/* Splitter */
QSplitter::handle {
    background-color: #1a1a1a;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #F97316;
}

/* ComboBox */
QComboBox {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 8px 12px;
}

QComboBox:hover {
    border-color: #F97316;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 8px;
    selection-background-color: #F97316;
}

/* Slider */
QSlider::groove:horizontal {
    background-color: #1a1a1a;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #F97316;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #FB923C;
}

/* Graphics View (Comic Viewer) */
QGraphicsView {
    background-color: #0a0a0a;
    border: none;
}

/* Dock Widget */
QDockWidget {
    color: #e0e0e0;
    titlebar-close-icon: none;
}

QDockWidget::title {
    background-color: #111111;
    padding: 8px;
    border-bottom: 1px solid #1a1a1a;
}

/* Group Box */
QGroupBox {
    color: #F97316;
    border: 1px solid #222222;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

/* Tooltips */
QToolTip {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Dialog */
QDialog {
    background-color: #0d0d0d;
}

/* Checkbox */
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #333333;
    background-color: #1a1a1a;
}

QCheckBox::indicator:checked {
    background-color: #F97316;
    border-color: #F97316;
}

/* Spin Box */
QSpinBox {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 6px 10px;
}

QSpinBox:focus {
    border-color: #F97316;
}
"""

LIGHT_THEME = """
/* ===== COMIO Light Theme ===== */

QWidget {
    background-color: #fafafa;
    color: #1a1a1a;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #fafafa;
}

QMenuBar {
    background-color: #ffffff;
    color: #1a1a1a;
    border-bottom: 1px solid #e5e5e5;
}

QMenuBar::item:selected {
    background-color: #F97316;
    color: #ffffff;
}

QMenu {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
}

QMenu::item:selected {
    background-color: #F97316;
    color: #ffffff;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5e5;
}

QToolButton {
    background-color: transparent;
    color: #1a1a1a;
    border-radius: 6px;
    padding: 8px 12px;
}

QToolButton:hover {
    background-color: #f0f0f0;
    color: #F97316;
}

QToolButton:checked {
    background-color: #F97316;
    color: #ffffff;
}

QScrollBar:vertical {
    background-color: #fafafa;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #cccccc;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #F97316;
}

QScrollBar:horizontal {
    background-color: #fafafa;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #cccccc;
    border-radius: 5px;
}

QStatusBar {
    background-color: #ffffff;
    color: #888888;
    border-top: 1px solid #e5e5e5;
}

QLineEdit {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 8px 12px;
}

QLineEdit:focus {
    border-color: #F97316;
}

QPushButton {
    background-color: #F97316;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #FB923C;
}

QGraphicsView {
    background-color: #f0f0f0;
    border: none;
}

QListWidget {
    background-color: #fafafa;
    border: none;
}

QListWidget::item:selected {
    background-color: #fff3e0;
    border: 1px solid #F97316;
}

QProgressBar {
    background-color: #e5e5e5;
    border-radius: 6px;
    height: 8px;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #F97316, stop:1 #FB923C);
    border-radius: 6px;
}

QSplitter::handle {
    background-color: #e5e5e5;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #F97316;
}

QToolTip {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 10px;
}
"""


def get_theme(name: str = "dark") -> str:
    """Return the QSS theme string by name."""
    if name == "light":
        return LIGHT_THEME
    return DARK_THEME

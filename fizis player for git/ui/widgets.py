from PyQt6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QMenu
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QAction
from PyQt6.QtWidgets import QMessageBox, QInputDialog


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._scale = 1.0
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._setup_base_styles()

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def _setup_base_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #bb86fc;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b66fc;
            }
            QPushButton:pressed {
                background-color: #7b46dc;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()

            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.95)
            self.animation.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()

            self.animation.setStartValue(0.95)
            self.animation.setEndValue(1.0)
            self.animation.start()

        super().mouseReleaseEvent(event)


class PlaylistsDropdown(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget { 
                background-color: #2d2d2d; 
                border: 2px solid #bb86fc; 
                border-radius: 15px; 
                color: white; 
            }
            QListWidget { 
                background-color: #2d2d2d; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 12px; 
                outline: none; 
            }
            QListWidget::item { 
                padding: 12px 15px; 
                border-bottom: 1px solid #3d3d3d; 
                background-color: transparent; 
                color: white; 
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:selected { 
                background-color: #bb86fc !important; 
                color: #000000 !important; 
                font-weight: bold; 
                border: none; 
            }
            QListWidget::item:hover:!selected { 
                background-color: #3d3d3d; 
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Ваши плейлисты")
        title.setStyleSheet("""
            color: #bb86fc; 
            font-weight: bold; 
            font-size: 14px; 
            padding: 8px;
            background-color: #2d2d2d;
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self.on_playlist_selected)
        self.playlists_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlists_list.customContextMenuRequested.connect(self.show_playlist_context_menu)
        layout.addWidget(self.playlists_list)

        self.add_button = AnimatedButton("Создать плейлист")
        self.add_button.setFixedHeight(35)
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 15px; 
                padding: 8px 12px; 
                font-weight: bold; 
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.add_button.clicked.connect(self.create_new_playlist)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        self.setFixedSize(250, 350)

    def update_playlists(self, playlists, current_playlist):
        self.playlists_list.clear()
        for name in playlists.keys():
            item = QListWidgetItem(name)
            if name == current_playlist:
                item.setBackground(QColor(187, 134, 252))
                item.setForeground(QColor(0, 0, 0))
                item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.playlists_list.addItem(item)

    def on_playlist_selected(self, item):
        playlist_name = item.text()
        self.parent.switch_playlist(playlist_name)
        self.hide()

    def show_playlist_context_menu(self, position):
        item = self.playlists_list.itemAt(position)
        if not item:
            return

        playlist_name = item.text()

        if playlist_name == "Основной":
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #bb86fc;
                color: black;
            }
        """)

        delete_action = QAction("Удалить плейлист", self)
        delete_action.triggered.connect(lambda: self.delete_playlist(playlist_name))
        menu.addAction(delete_action)

        menu.exec(self.playlists_list.mapToGlobal(position))

    def delete_playlist(self, playlist_name):
        reply = QMessageBox.question(
            self,
            "Удаление плейлиста",
            f"Вы уверены, что хотите удалить плейлист '{playlist_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.parent.delete_playlist(playlist_name)
            self.hide()

    def create_new_playlist(self):
        self.parent.show_add_playlist_dialog()
        self.hide()

    def mousePressEvent(self, event):
        self.hide()
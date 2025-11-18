import os
import random
import shutil
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QListWidget, QLabel, QSlider, QStackedWidget,
                            QSplitter, QFileDialog, QMessageBox, QInputDialog,
                            QMenu, QListWidgetItem, QDialog)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QColor, QFont, QAction, QPixmap, QPainter, QPen, QBrush
from core.auth import AuthManager
from ui.widgets import AnimatedButton, PlaylistsDropdown
from ui.dialogs import AuthWidget
from utils.helpers import get_app_icon, format_time


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.current_user = None
        self.playlists = {}
        self.current_playlist = "Основной"
        self.current_track_index = 0
        self.is_shuffle = False
        self.is_repeat = False
        self.volume = 50
        self.current_playing_item = None
        self.is_playing = False
        self.playback_finished = False

        icon = get_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.setWindowTitle("fplay")
        self.setMinimumSize(900, 700)

        self.setup_ui()
        self.setup_player()
        self.check_session()

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #1a1a1a; 
                color: white; 
            }
            QWidget { 
                background-color: #1a1a1a; 
                color: white; 
            }
            QLabel { 
                color: white; 
            }
            QListWidget { 
                background-color: #2d2d2d; 
                color: white; 
                border: 2px solid #bb86fc; 
                border-radius: 15px; 
                padding: 5px; 
            }
            QListWidget::item { 
                padding: 12px 15px; 
                border-bottom: 1px solid #3d3d3d; 
                border-radius: 8px;
                margin: 2px;
            }
            QListWidget::item:hover { 
                background-color: #3d3d3d; 
            }
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
            QSlider::groove:horizontal { 
                background: #2d2d2d; 
                height: 8px; 
                border-radius: 4px; 
            }
            QSlider::handle:horizontal { 
                background: #bb86fc; 
                width: 18px; 
                height: 18px; 
                border-radius: 9px; 
                margin: -5px 0; 
            }
            QSlider::handle:horizontal:hover { 
                background: #9b66fc; 
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.auth_widget = AuthWidget(self.auth_manager, self)
        self.stacked_widget.addWidget(self.auth_widget)

        self.player_widget = QWidget()
        player_layout = QVBoxLayout()
        player_layout.setSpacing(15)
        player_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()

        self.user_container = QWidget()
        user_container_layout = QHBoxLayout()
        user_container_layout.setContentsMargins(0, 0, 0, 0)
        user_container_layout.setSpacing(8)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(32, 32)
        self.avatar_label.setStyleSheet("""
            border-radius: 16px; 
            background-color: #2d2d2d; 
            border: 2px solid #bb86fc;
        """)
        self.avatar_label.setScaledContents(True)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_container_layout.addWidget(self.avatar_label)

        self.user_label = QLabel("Не авторизован")
        self.user_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 14px; 
            font-weight: bold; 
            cursor: pointer; 
        """)
        self.user_label.mousePressEvent = self.on_user_label_clicked
        user_container_layout.addWidget(self.user_label)

        self.user_container.setLayout(user_container_layout)
        header_layout.addWidget(self.user_container)

        header_layout.addStretch()

        self.playlist_dropdown_btn = AnimatedButton("Плейлисты")
        self.playlist_dropdown_btn.setFixedSize(120, 40)
        self.playlist_dropdown_btn.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 20px; 
                font-size: 14px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.playlist_dropdown_btn.clicked.connect(self.show_playlists_dropdown)
        header_layout.addWidget(self.playlist_dropdown_btn)

        self.add_track_btn = AnimatedButton("Добавить трек")
        self.add_track_btn.setFixedSize(120, 40)
        self.add_track_btn.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 20px; 
                font-size: 14px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.add_track_btn.clicked.connect(self.show_add_track_dialog)
        header_layout.addWidget(self.add_track_btn)

        player_layout.addLayout(header_layout)

        self.playlist_label = QLabel("Плейлист: Основной")
        self.playlist_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 16px; 
            font-weight: bold;
            padding: 10px;
            background-color: #2d2d2d;
            border-radius: 10px;
            border: 1px solid #bb86fc;
        """)
        self.playlist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_layout.addWidget(self.playlist_label)

        self.tracks_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tracks_splitter.setChildrenCollapsible(False)
        self.tracks_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bb86fc;
                width: 3px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: #9b66fc;
            }
        """)

        self.tracks_list = QListWidget()
        self.tracks_list.itemClicked.connect(self.on_track_clicked)
        self.tracks_list.itemDoubleClicked.connect(self.play_selected_track)
        self.tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks_list.customContextMenuRequested.connect(self.show_track_context_menu)
        self.tracks_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #bb86fc;
                border-radius: 15px;
                padding: 8px;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #3d3d3d;
                background-color: transparent;
                border-radius: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        self.tracks_splitter.addWidget(self.tracks_list)

        self.profile_stats_widget = QWidget()
        self.profile_stats_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #bb86fc;
                border-radius: 15px;
                padding: 15px;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
        profile_stats_layout = QVBoxLayout()
        profile_stats_layout.setContentsMargins(10, 10, 10, 10)
        profile_stats_layout.setSpacing(15)

        stats_title = QLabel("Статистика профиля")
        stats_title.setStyleSheet("""
            color: #bb86fc;
            font-size: 18px;
            font-weight: bold;
            padding: 5px;
            border-bottom: 2px solid #bb86fc;
        """)
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_stats_layout.addWidget(stats_title)

        self.total_tracks_label = QLabel("Всего треков: 0")
        self.total_tracks_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_tracks_label)

        self.total_playlists_label = QLabel("Плейлистов: 0")
        self.total_playlists_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_playlists_label)

        self.total_duration_label = QLabel("Общее время: 0:00")
        self.total_duration_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        profile_stats_layout.addWidget(self.total_duration_label)

        profile_stats_layout.addStretch()

        self.profile_stats_widget.setLayout(profile_stats_layout)
        self.tracks_splitter.addWidget(self.profile_stats_widget)

        self.profile_stats_widget.hide()
        self.tracks_splitter.setSizes([1000, 0])

        player_layout.addWidget(self.tracks_splitter, 1)

        self.current_track_label = QLabel("Трек не выбран")
        self.current_track_label.setStyleSheet("""
            color: #bb86fc; 
            font-size: 12px; 
            padding: 8px; 
            background-color: #2d2d2d; 
            border-radius: 8px;
            border: 1px solid #bb86fc;
            font-weight: bold;
        """)
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_layout.addWidget(self.current_track_label)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(100)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        player_layout.addWidget(self.position_slider)

        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: #bb86fc; font-size: 11px;")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: #bb86fc; font-size: 11px;")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        player_layout.addLayout(time_layout)

        controls_layout = QHBoxLayout()
        controls_layout.addStretch()

        self.repeat_button = AnimatedButton("↻")
        self.repeat_button.setFixedSize(100, 50)
        self.repeat_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 24px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        controls_layout.addWidget(self.repeat_button)

        self.prev_button = AnimatedButton("◀◀")
        self.prev_button.setFixedSize(100, 50)
        self.prev_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 18px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.prev_button.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_button)

        self.play_pause_button = AnimatedButton("▶")
        self.play_pause_button.setFixedSize(100, 60)
        self.play_pause_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 30px; 
                font-size: 28px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_button)

        self.next_button = AnimatedButton("▶▶")
        self.next_button.setFixedSize(100, 50)
        self.next_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 18px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
            QPushButton:pressed { 
                background-color: #7b46dc; 
            }
        """)
        self.next_button.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_button)

        self.shuffle_button = AnimatedButton("⇄")
        self.shuffle_button.setFixedSize(100, 50)
        self.shuffle_button.setStyleSheet("""
            QPushButton { 
                background-color: #bb86fc; 
                color: black; 
                border: none; 
                border-radius: 25px; 
                font-size: 24px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #9b66fc; 
            }
        """)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        controls_layout.addWidget(self.shuffle_button)

        controls_layout.addStretch()

        volume_layout = QHBoxLayout()
        volume_layout.addStretch()
        volume_layout.setSpacing(9)

        volume_icon = QLabel("♪")
        volume_icon.setStyleSheet("color: #bb86fc; font-size: 14px; font-weight: bold;")
        volume_icon.setFixedWidth(19)
        volume_layout.addWidget(volume_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("50%")
        self.volume_label.setStyleSheet("color: #bb86fc; font-size: 11px; font-weight: bold;")
        self.volume_label.setFixedWidth(30)
        volume_layout.addWidget(self.volume_label)

        controls_layout.addLayout(volume_layout)

        player_layout.addLayout(controls_layout)

        self.player_widget.setLayout(player_layout)
        self.stacked_widget.addWidget(self.player_widget)

        self.playlists_dropdown = PlaylistsDropdown(self)

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(100)

        self.slider_pressed = False

    def setup_player(self):
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished = True
            self.handle_playback_finished()

    def handle_playback_finished(self):
        if self.playback_finished:
            self.playback_finished = False
            if self.is_repeat:
                self.play_current_track()
            else:
                if (self.current_playlist in self.playlists and
                        self.current_track_index < len(self.playlists[self.current_playlist]) - 1):
                    self.play_next()
                else:
                    self.current_track_index = 0
                    self.play_current_track()

    def on_track_clicked(self, item):
        track_data = item.data(Qt.ItemDataRole.UserRole)
        index = self.tracks_list.row(item)

        self.current_track_index = index
        self.highlight_current_track()

        if isinstance(track_data, dict):
            if track_data.get('local_file') and track_data.get('file_path'):
                if os.path.exists(track_data['file_path']):
                    self.play_track(track_data['file_path'])
                else:
                    self.play_streaming_track(track_data)
            else:
                self.play_streaming_track(track_data)
        else:
            track_path = track_data
            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return
            self.play_track(track_path)

    def check_session(self):
        token = self.auth_manager.load_session_token()
        if token:
            user = self.auth_manager.validate_session(token)
            if user:
                self.on_login_success(user)
                return
        self.stacked_widget.setCurrentIndex(0)

    def on_login_success(self, user):
        self.current_user = user
        self.user_label.setText(f"{user['username']}")

        if user.get('avatar_path'):
            self.load_user_avatar(user['avatar_path'], self.avatar_label)
        else:
            self.set_default_avatar(self.avatar_label)

        self.stacked_widget.setCurrentIndex(1)

        if user.get('id'):
            settings = self.auth_manager.load_user_settings(user['id'])
            self.volume = settings.get('volume', 50)
            self.volume_slider.setValue(self.volume)
            self.set_volume(self.volume)
            self.is_repeat = settings.get('repeat_mode', False)
            self.is_shuffle = settings.get('shuffle_mode', False)
            self.current_playlist = settings.get('current_playlist', 'Основной')

            self.playlists = self.auth_manager.load_user_playlists(user['id'])
            if not self.playlists:
                self.playlists = {'Основной': []}
            self.update_playlist_display()

            self.repeat_button.setText("↻●" if self.is_repeat else "↻")
            self.shuffle_button.setText("⇄●" if self.is_shuffle else "⇄")

        self.tracks_splitter.splitterMoved.connect(self.on_splitter_moved)

    def on_splitter_moved(self, pos, index):
        sizes = self.tracks_splitter.sizes()
        if sizes[1] > 50:
            if not self.profile_stats_widget.isVisible():
                self.profile_stats_widget.show()
        else:
            if self.profile_stats_widget.isVisible():
                self.profile_stats_widget.hide()

    def update_profile_stats(self):
        if not self.current_user:
            return

        total_tracks = 0
        total_playlists = len(self.playlists)
        total_duration_seconds = 0

        for playlist_name, tracks in self.playlists.items():
            total_tracks += len(tracks)
            for track in tracks:
                if isinstance(track, dict):
                    if 'duration' in track:
                        duration_str = track.get('duration', '0:00')
                        try:
                            parts = duration_str.split(':')
                            if len(parts) == 2:
                                minutes, seconds = map(int, parts)
                                total_duration_seconds += minutes * 60 + seconds
                        except:
                            pass
                elif isinstance(track, str) and os.path.exists(track):
                    pass

        self.total_tracks_label.setText(f"Всего треков: {total_tracks}")
        self.total_playlists_label.setText(f"Плейлистов: {total_playlists}")

        hours = total_duration_seconds // 3600
        minutes = (total_duration_seconds % 3600) // 60
        if hours > 0:
            self.total_duration_label.setText(f"Общее время: {hours}:{minutes:02d}:00")
        else:
            self.total_duration_label.setText(f"Общее время: {minutes}:00")

    def handle_logout(self):
        self.auth_manager.logout()
        self.current_user = None
        self.playlists = {}
        self.current_playlist = "Основной"
        self.tracks_list.clear()
        self.stacked_widget.setCurrentIndex(0)
        self.stop()

    def show_playlists_dropdown(self):
        if self.current_user:
            self.playlists_dropdown.update_playlists(self.playlists, self.current_playlist)
            button_pos = self.playlist_dropdown_btn.mapToGlobal(self.playlist_dropdown_btn.rect().bottomLeft())
            self.playlists_dropdown.move(button_pos)
            self.playlists_dropdown.show()

    def show_add_playlist_dialog(self):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Введите название плейлиста:")
        if ok and name.strip():
            if name.strip() not in self.playlists:
                self.playlists[name.strip()] = []
                self.current_playlist = name.strip()
                self.playlist_label.setText(f"Плейлист: {self.current_playlist}")
                self.save_playlists()
                self.update_playlist_display()
                QMessageBox.information(self, "Успех", f"Плейлист '{name.strip()}' создан")
            else:
                QMessageBox.warning(self, "Ошибка", "Плейлист с таким именем уже существует")

    def delete_playlist(self, playlist_name):
        if playlist_name not in self.playlists:
            return

        if playlist_name == "Основной":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить основной плейлист")
            return

        if self.current_playlist == playlist_name:
            self.current_playlist = "Основной"
            self.playlist_label.setText(f"Плейлист: {self.current_playlist}")

        del self.playlists[playlist_name]

        if self.current_user and self.current_user.get('id'):
            self.auth_manager.delete_playlist(self.current_user['id'], playlist_name)
            self.save_playlists()

        self.update_playlist_display()
        QMessageBox.information(self, "Успех", f"Плейлист '{playlist_name}' удален")

    def switch_playlist(self, playlist_name):
        if playlist_name in self.playlists:
            self.current_playlist = playlist_name
            self.playlist_label.setText(f"Плейлист: {self.current_playlist}")
            self.update_playlist_display()
            if self.current_user:
                settings = self.auth_manager.load_user_settings(self.current_user['id'])
                settings['current_playlist'] = playlist_name
                self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def update_playlist_display(self):
        self.tracks_list.clear()
        self.current_playing_item = None

        if self.current_playlist in self.playlists:
            for i, track in enumerate(self.playlists[self.current_playlist]):
                if isinstance(track, dict):
                    if track.get('type') == 'youtube':
                        title = track.get('title', 'Unknown YouTube track')
                        artist = track.get('artist', 'Unknown Artist')
                        source = track.get('source', 'YouTube')
                        downloaded = " ✅" if track.get('downloaded') else ""
                        item_text = f"🎵 {artist} - {title}{downloaded}"
                        item = QListWidgetItem(item_text)
                        item.setToolTip(f"YouTube: {title}\nИсполнитель: {artist}\nИсточник: {source}")
                        item.setData(Qt.ItemDataRole.UserRole, track)
                    elif track.get('type') == 'telegram':
                        title = track.get('title', 'Unknown Telegram track')
                        artist = track.get('artist', 'Unknown Artist')
                        item_text = f"{artist} - {title}"
                        item = QListWidgetItem(item_text)
                        item.setToolTip(f"AudioBot: {title}\nИсполнитель: {artist}")
                        item.setData(Qt.ItemDataRole.UserRole, track)
                else:
                    track_path = track
                    track_name = os.path.basename(track_path)
                    item_text = track_name
                    item = QListWidgetItem(item_text)
                    item.setToolTip(f"Локальный файл: {track_name}")
                    item.setData(Qt.ItemDataRole.UserRole, track_path)

                self.tracks_list.addItem(item)

        self.highlight_current_track()
        self.update_profile_stats()

    def highlight_current_track(self):
        for i in range(self.tracks_list.count()):
            item = self.tracks_list.item(i)
            if item:
                if i == self.current_track_index:
                    item.setBackground(QColor(45, 45, 45))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                    self.current_playing_item = item
                    self.tracks_list.scrollToItem(item, QListWidget.ScrollHint.EnsureVisible)
                else:
                    item.setBackground(QColor(0, 0, 0, 0))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 10, QFont.Weight.Normal))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите аудио файлы", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*)"
        )
        if files:
            self.add_tracks_to_playlist(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой")
        if folder:
            audio_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
                        audio_files.append(os.path.join(root, file))
            if audio_files:
                self.add_tracks_to_playlist(audio_files)
            else:
                QMessageBox.information(self, "Информация", "В выбранной папке не найдено аудио файлов")

    def add_tracks_to_playlist(self, files):
        if self.current_playlist not in self.playlists:
            self.playlists[self.current_playlist] = []
        for file_path in files:
            if file_path not in self.playlists[self.current_playlist]:
                self.playlists[self.current_playlist].append(file_path)
        self.update_playlist_display()
        self.save_playlists()

    def save_playlists(self):
        if self.current_user and self.current_user.get('id'):
            self.auth_manager.save_user_playlists(self.current_user['id'], self.playlists)

    def play_selected_track(self, item):
        self.on_track_clicked(item)

    def play_current_track(self):
        if (self.current_playlist in self.playlists and
                self.current_track_index < len(self.playlists[self.current_playlist])):

            track = self.playlists[self.current_playlist][self.current_track_index]

            if isinstance(track, dict):
                if track.get('local_file') and track.get('file_path'):
                    if os.path.exists(track['file_path']):
                        self.play_track(track['file_path'])
                    else:
                        self.play_streaming_track(track)
                else:
                    self.play_streaming_track(track)
            else:
                if os.path.exists(track):
                    self.play_track(track)
                else:
                    QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track}")

    def play_streaming_track(self, track_data):
        try:
            if track_data.get('type') == 'youtube':
                title = track_data.get('title', 'YouTube трек')
                artist = track_data.get('artist', 'Неизвестный исполнитель')
                self.current_track_label.setText(f"🎵 {artist} - {title}")

                if track_data.get('downloaded') and track_data.get('file_path'):
                    if os.path.exists(track_data['file_path']):
                        self.play_track(track_data['file_path'])
                        return

                QMessageBox.information(
                    self,
                    "YouTube Music",
                    f"Трек: {track_data.get('title', 'Неизвестный')}\n"
                    f"Исполнитель: {track_data.get('artist', 'Неизвестный')}\n\n"
                    "Скачайте трек для воспроизведения."
                )
            else:
                self.current_track_label.setText(f"♪ {track_data.get('title', 'Стриминговый трек')}")

        except Exception as e:
            print(f"Ошибка воспроизведения стримингового трека: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось воспроизвести трек: {str(e)}")

    def play_track(self, track_path):
        try:
            if isinstance(track_path, dict):
                self.play_streaming_track(track_path)
                return

            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return

            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()

            QTimer.singleShot(100, lambda: self._actually_play_track(track_path))

        except Exception as e:
            print(f"Ошибка в play_track: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка воспроизведения: {str(e)}")

    def _actually_play_track(self, track_path):
        try:
            if not os.path.exists(track_path):
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {track_path}")
                return

            file_url = QUrl.fromLocalFile(track_path)

            if not file_url.isValid():
                QMessageBox.warning(self, "Ошибка", f"Неверный URL файла: {track_path}")
                return

            self.media_player.setSource(file_url)

            if self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.InvalidMedia:
                QMessageBox.warning(self, "Ошибка", f"Неподдерживаемый формат файла: {track_path}")
                return

            self.media_player.play()
            self.is_playing = True
            track_name = os.path.basename(track_path)
            self.current_track_label.setText(f"▶ {track_name}")

            self.highlight_current_track()

        except Exception as e:
            print(f"Ошибка в _actually_play_track: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка воспроизведения: {str(e)}")

    def toggle_play_pause(self):
        try:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_pause_button.setText("▶")
                self.is_playing = False
            else:
                if self.media_player.source().isEmpty():
                    if (self.current_playlist in self.playlists and
                            self.playlists[self.current_playlist] and
                            self.current_track_index >= 0):
                        self.play_current_track()
                    else:
                        QMessageBox.information(self, "Информация", "Нет треков в плейлисте")
                else:
                    self.media_player.play()
                    self.play_pause_button.setText("❚❚")
                    self.is_playing = True

        except Exception as e:
            print(f"Ошибка в toggle_play_pause: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка управления воспроизведением: {str(e)}")

    def pause(self):
        self.media_player.pause()
        self.play_pause_button.setText("▶")
        self.is_playing = False

    def stop(self):
        self.media_player.stop()
        self.current_track_label.setText("Трек не выбран")
        self.position_slider.setValue(0)
        self.play_pause_button.setText("▶")
        self.is_playing = False

    def play_next(self):
        try:
            if self.current_playlist in self.playlists and self.playlists[self.current_playlist]:
                if self.is_shuffle:
                    self.current_track_index = random.randint(0, len(self.playlists[self.current_playlist]) - 1)
                else:
                    self.current_track_index = (self.current_track_index + 1) % len(
                        self.playlists[self.current_playlist])

                self.play_current_track()

        except Exception as e:
            print(f"Ошибка в play_next: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка переключения трека: {str(e)}")

    def play_previous(self):
        try:
            if self.current_playlist in self.playlists and self.playlists[self.current_playlist]:
                if self.is_shuffle:
                    self.current_track_index = random.randint(0, len(self.playlists[self.current_playlist]) - 1)
                else:
                    self.current_track_index = (self.current_track_index - 1) % len(
                        self.playlists[self.current_playlist])

                self.play_current_track()

        except Exception as e:
            print(f"Ошибка в play_previous: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка переключения трека: {str(e)}")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        self.shuffle_button.setText("⇄●" if self.is_shuffle else "⇄")

        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['shuffle_mode'] = self.is_shuffle
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self.repeat_button.setText("↻●" if self.is_repeat else "↻")

        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['repeat_mode'] = self.is_repeat
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def set_volume(self, value):
        self.volume = value
        self.audio_output.setVolume(value / 100.0)
        self.volume_label.setText(f"{value}%")
        if self.current_user and self.current_user.get('id'):
            settings = self.auth_manager.load_user_settings(self.current_user['id'])
            settings['volume'] = value
            self.auth_manager.save_user_settings(self.current_user['id'], settings)

    def on_position_changed(self, position):
        if not self.slider_pressed:
            duration = self.media_player.duration()
            if duration > 0:
                self.position_slider.setValue(int((position / duration) * 100))
                self.current_time_label.setText(self.format_time(position))

    def on_duration_changed(self, duration):
        if duration > 0:
            self.position_slider.setMaximum(100)
            self.total_time_label.setText(self.format_time(duration))

    def on_playback_state_changed(self, state):
        try:
            if state == QMediaPlayer.PlaybackState.PlayingState:
                self.play_pause_button.setText("❚❚")
                self.is_playing = True
            elif state == QMediaPlayer.PlaybackState.PausedState:
                self.play_pause_button.setText("▶")
                self.is_playing = False
            elif state == QMediaPlayer.PlaybackState.StoppedState:
                self.play_pause_button.setText("▶")
                self.is_playing = False

        except Exception as e:
            print(f"Ошибка в on_playback_state_changed: {e}")

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def update_position(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            pass

    def on_slider_pressed(self):
        self.slider_pressed = True

    def on_slider_released(self):
        self.slider_pressed = False
        if self.media_player.duration() > 0:
            position = int((self.position_slider.value() / 100.0) * self.media_player.duration())
            self.media_player.setPosition(position)

    def on_user_label_clicked(self, event):
        if self.current_user:
            self.show_account_menu(event)

    def show_account_menu(self, event):
        if not self.current_user:
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

        change_avatar_action = QAction("Изменить аватарку", self)
        change_avatar_action.triggered.connect(self.change_avatar)
        menu.addAction(change_avatar_action)

        change_name_action = QAction("Изменить имя", self)
        change_name_action.triggered.connect(self.change_username)
        menu.addAction(change_name_action)

        menu.addSeparator()

        logout_action = QAction("Выйти из аккаунта", self)
        logout_action.triggered.connect(self.handle_logout)
        menu.addAction(logout_action)

        menu.exec(self.user_label.mapToGlobal(self.user_label.rect().bottomLeft()))

    def show_track_context_menu(self, position):
        item = self.tracks_list.itemAt(position)
        if not item:
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

        play_action = QAction("Воспроизвести", self)
        play_action.triggered.connect(lambda: self.play_selected_track(item))
        menu.addAction(play_action)

        menu.addSeparator()

        remove_action = QAction("Удалить из плейлиста", self)
        remove_action.triggered.connect(lambda: self.remove_track_from_playlist(item))
        menu.addAction(remove_action)

        menu.exec(self.tracks_list.mapToGlobal(position))

    def remove_track_from_playlist(self, item):
        index = self.tracks_list.row(item)
        if (self.current_playlist in self.playlists and
                index < len(self.playlists[self.current_playlist])):

            if index == self.current_track_index:
                self.stop()
                self.current_track_index = -1

            del self.playlists[self.current_playlist][index]

            self.update_playlist_display()
            self.save_playlists()

            QMessageBox.information(self, "Успех", "Трек удален из плейлиста")

    def load_user_avatar(self, avatar_path, avatar_label):
        try:
            if avatar_path and os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)
                    rounded_pixmap = QPixmap(32, 32)
                    rounded_pixmap.fill(Qt.GlobalColor.transparent)

                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(QPen(QColor(187, 134, 252), 2))
                    painter.drawEllipse(0, 0, 32, 32)
                    painter.end()

                    avatar_label.setPixmap(rounded_pixmap)
                    return
        except Exception as e:
            print(f"Ошибка загрузки аватарки: {e}")
        self.set_default_avatar(avatar_label)

    def set_default_avatar(self, avatar_label):
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(45, 45, 45))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(187, 134, 252), 2))
            painter.setBrush(QBrush(QColor(187, 134, 252)))

            painter.drawEllipse(4, 4, 24, 24)

            painter.setPen(QColor(26, 26, 26))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            if self.current_user and self.current_user.get('username'):
                initial = self.current_user['username'][0].upper()
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial)
            painter.end()

            avatar_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Ошибка создания дефолтной аватарки: {e}")

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аватарку", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path and self.current_user and self.current_user.get('id'):
            avatars_dir = os.path.join(os.path.dirname(__file__), "..", "avatars")
            os.makedirs(avatars_dir, exist_ok=True)

            file_ext = os.path.splitext(file_path)[1]
            new_filename = f"avatar_{self.current_user['id']}{file_ext}"
            new_path = os.path.join(avatars_dir, new_filename)

            try:
                shutil.copy2(file_path, new_path)
                self.auth_manager.update_avatar(self.current_user['id'], new_path)

                self.current_user['avatar_path'] = new_path
                self.load_user_avatar(new_path, self.avatar_label)

                QMessageBox.information(self, "Успех", "Аватарка изменена")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось изменить аватарку:\n{str(e)}")

    def change_username(self):
        if not self.current_user:
            return

        new_username, ok = QInputDialog.getText(
            self, "Изменить имя", "Введите новое имя:",
            text=self.current_user.get('username', '')
        )

        if ok and new_username.strip() and self.current_user.get('id'):
            if self.auth_manager.update_username(self.current_user['id'], new_username.strip()):
                self.current_user['username'] = new_username.strip()
                self.user_label.setText(f"{self.current_user['username']}")

                if not self.current_user.get('avatar_path'):
                    self.set_default_avatar(self.avatar_label)

                QMessageBox.information(self, "Успех", "Имя изменено")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить имя")

    def show_add_track_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить трек")
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: white; }
            QLabel { color: white; font-size: 14px; }
            QPushButton { background-color: #bb86fc; color: black; border: none; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #9b66fc; }
            QLineEdit { background-color: #2d2d2d; color: white; border: 2px solid #bb86fc; border-radius: 8px; padding: 10px; }
        """)

        layout = QVBoxLayout()

        title = QLabel("Добавить трек")
        title.setStyleSheet("color: #bb86fc; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        from_device_btn = AnimatedButton("С устройства")
        from_device_btn.clicked.connect(lambda: self.add_from_device(dialog))
        layout.addWidget(from_device_btn)

        add_folder_btn = AnimatedButton("Добавить папку")
        add_folder_btn.clicked.connect(lambda: self.add_folder_from_dialog(dialog))
        layout.addWidget(add_folder_btn)

        layout.addStretch()

        close_btn = AnimatedButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def add_from_device(self, dialog):
        dialog.accept()
        self.add_files()

    def add_folder_from_dialog(self, dialog):
        dialog.accept()
        self.add_folder()
import os
import random
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWidgets import QMessageBox


class MusicPlayerCore:
    def __init__(self):
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.is_playing = False
        self.playback_finished = False

        # Подключаем сигналы
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
            # Логика перехода к следующему треку будет в главном окне

    def play_track(self, track_path):
        try:
            if not os.path.exists(track_path):
                return False, f"Файл не найден: {track_path}"

            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()

            file_url = QUrl.fromLocalFile(track_path)

            if not file_url.isValid():
                return False, f"Неверный URL файла: {track_path}"

            self.media_player.setSource(file_url)

            if self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.InvalidMedia:
                return False, f"Неподдерживаемый формат файла: {track_path}"

            self.media_player.play()
            self.is_playing = True
            return True, "Трек воспроизводится"

        except Exception as e:
            return False, f"Ошибка воспроизведения: {str(e)}"

    def toggle_play_pause(self):
        try:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.is_playing = False
                return "pause"
            else:
                if not self.media_player.source().isEmpty():
                    self.media_player.play()
                    self.is_playing = True
                    return "play"
                else:
                    return "no_track"
        except Exception as e:
            print(f"Ошибка переключения воспроизведения: {e}")
            return "error"

    def stop(self):
        self.media_player.stop()
        self.is_playing = False

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def get_position(self):
        return self.media_player.position()

    def get_duration(self):
        return self.media_player.duration()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def on_position_changed(self, position):
        # Этот метод будет переопределен в главном окне
        pass

    def on_duration_changed(self, duration):
        # Этот метод будет переопределен в главном окне
        pass

    def on_playback_state_changed(self, state):
        # Этот метод будет переопределен в главном окне
        pass